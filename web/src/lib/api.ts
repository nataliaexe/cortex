/**
 * Cliente HTTP do backend Cortex.
 */

const BASE = '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, init);
  if (!r.ok) {
    const detail = await r.text();
    throw new Error(`${r.status}: ${detail}`);
  }
  if (r.status === 204) return undefined as T;
  return r.json();
}

// ---------- health / providers ----------

export interface ProviderStatus {
  name: string;
  enabled: boolean;
  available: boolean;
  reason: string;
}

export const fetchHealth = () => request<{ status: string; version: string; providers_available: string[] }>('/health');
export const fetchProviders = () => request<ProviderStatus[]>('/providers');

// ---------- sessions / messages ----------

export interface Session {
  id: string;
  created_at: string;
  updated_at: string;
  title: string | null;
  metadata: Record<string, unknown>;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

export const fetchSessions = () => request<Session[]>('/sessions');
export const fetchMessages = (sessionId: string) => request<Message[]>(`/sessions/${sessionId}/messages`);

// ---------- projects ----------

export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

export const fetchProjects = () => request<Project[]>('/projects');

// ---------- chat ----------

export interface ChatResponse {
  session_id: string;
  text: string;
  provider: string;
  model: string;
  was_multi_intent: boolean;
  tool_calls: ToolCall[];
  dry_runs_pending: DryRun[];
}

export interface ToolCall {
  tool: string;
  args: Record<string, unknown>;
  ok: boolean;
  output: string;
  error: string | null;
}

export interface DryRun {
  tool: string;
  description: string;
  impact: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  project_id?: string;
  mode?: string;
  auto_confirm?: boolean;
  stream?: boolean;
}

export interface StreamCallbacks {
  onSession?: (sessionId: string) => void;
  onPlan?: (steps: PlanStep[]) => void;
  onDecision?: (data: DecisionEvent) => void;
  onToolResult?: (data: ToolCall) => void;
  onToken?: (text: string) => void;
  onDone?: (data: ChatResponse) => void;
  onError?: (message: string) => void;
}

export interface PlanStep {
  description: string;
  tool: string | null;
  done: boolean;
}

export interface DecisionEvent {
  tool?: string;
  decision?: string;
  reason?: string;
  critic_approved?: boolean;
  critic_reason?: string;
}

export function streamChat(payload: ChatRequest, callbacks: StreamCallbacks): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const r = await fetch(BASE + '/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!r.ok) {
        const detail = await r.text();
        callbacks.onError?.(`HTTP ${r.status}: ${detail}`);
        return;
      }

      if (!r.body) {
        callbacks.onError?.('sem corpo na resposta');
        return;
      }

      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let idx: number;
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const raw = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          parseSseEvent(raw, callbacks);
        }
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        callbacks.onError?.((e as Error).message);
      }
    }
  })();

  return () => controller.abort();
}

function parseSseEvent(raw: string, cb: StreamCallbacks) {
  const lines = raw.split('\n');
  let event = '';
  let data = '';
  for (const line of lines) {
    if (line.startsWith('event: ')) event = line.slice(7).trim();
    else if (line.startsWith('data: ')) data += line.slice(6);
  }
  if (!event || !data) return;

  let parsed: any;
  try { parsed = JSON.parse(data); } catch { return; }

  switch (event) {
    case 'session': cb.onSession?.(parsed.session_id); break;
    case 'plan': cb.onPlan?.(parsed.steps || []); break;
    case 'decision': cb.onDecision?.(parsed); break;
    case 'tool_result': cb.onToolResult?.(parsed); break;
    case 'token': cb.onToken?.(parsed.text || ''); break;
    case 'done': cb.onDone?.(parsed); break;
    case 'error': cb.onError?.(parsed.message || 'erro'); break;
  }
}

// ---------- calendar ----------

export interface CalendarEvent {
  id: string;
  title: string;
  description: string | null;
  location: string | null;
  start_at: string;
  end_at: string;
  all_day: boolean;
  source: string;
  recurrence: string;
  recurrence_days: number[] | null;
  recurrence_until: string | null;
  parent_id: string | null;
}

export interface OverlapWarning {
  with_id: string;
  with_title: string;
  with_start: string;
  with_end: string;
}

export interface CreateEventResponse {
  event: CalendarEvent;
  overlaps: OverlapWarning[];
}

export interface CreateEventPayload {
  title: string;
  start: string;
  end?: string;
  duration_minutes?: number;
  description?: string;
  location?: string;
  recurrence?: string;
  recurrence_days?: number[];
  recurrence_until?: string;
}

export const fetchCalendarEvents = (range: string = 'semana') =>
  request<CalendarEvent[]>(`/calendar/events?range=${encodeURIComponent(range)}`);

export const createCalendarEvent = (payload: CreateEventPayload) =>
  request<CreateEventResponse>('/calendar/events', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

export const deleteCalendarEvent = (id: string) =>
  request<void>(`/calendar/events/${id}`, { method: 'DELETE' });

export const syncCalendar = (daysAhead = 30) =>
  request<{ inserted: number; updated: number; total: number }>(`/calendar/sync?days_ahead=${daysAhead}`, { method: 'POST' });

// ---------- notes ----------

export interface Note {
  id: string;
  title: string | null;
  content: string;
  tags: string | null;
  created_at: string;
  updated_at: string;
  project_id: string | null;
}

export const fetchNotes = (params: { limit?: number; search?: string; tag?: string } = {}) => {
  const qs = new URLSearchParams();
  if (params.limit) qs.set('limit', String(params.limit));
  if (params.search) qs.set('search', params.search);
  if (params.tag) qs.set('tag', params.tag);
  const suffix = qs.toString() ? `?${qs}` : '';
  return request<Note[]>(`/notes${suffix}`);
};

export const createNote = (payload: { content: string; title?: string; tags?: string[] }) =>
  request<Note>('/notes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

export const deleteNote = (id: string) =>
  request<void>(`/notes/${id}`, { method: 'DELETE' });

// ---------- memory ----------

export interface EpisodicEntry {
  id: string;
  session_id: string;
  ts: string;
  summary: string;
  content: string;
  tags: string | null;
  importance: number;
  project_id: string | null;
}

export interface SemanticEntry {
  id: string;
  key: string;
  value: string;
  source: string | null;
  confidence: number;
  updated_at: string;
  project_id: string | null;
}

export interface MemoryStats {
  [key: string]: number;
}

export const fetchEpisodic = (limit = 50, projectId?: string) => {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (projectId) qs.set('project_id', projectId);
  return request<EpisodicEntry[]>(`/memory/episodic?${qs}`);
};

export const fetchSemantic = (limit = 100, projectId?: string) => {
  const qs = new URLSearchParams({ limit: String(limit) });
  if (projectId) qs.set('project_id', projectId);
  return request<SemanticEntry[]>(`/memory/semantic?${qs}`);
};

export const fetchMemoryStats = () => request<MemoryStats>('/memory/stats');

// ---------- audit ----------

export interface AuditEntry {
  id: string;
  ts: string;
  tool: string;
  args: Record<string, unknown>;
  decision: string;
  reason: string | null;
  result: string | null;
  session_id: string | null;
  project_id: string | null;
}

export const fetchAudit = (params: {
  limit?: number;
  decision?: string;
  tool?: string;
} = {}) => {
  const qs = new URLSearchParams();
  if (params.limit) qs.set('limit', String(params.limit));
  if (params.decision) qs.set('decision', params.decision);
  if (params.tool) qs.set('tool', params.tool);
  const suffix = qs.toString() ? `?${qs}` : '';
  return request<AuditEntry[]>(`/audit${suffix}`);
};
