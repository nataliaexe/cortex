export interface ToolCallDisplay {
  id: string;
  tool: string;
  args: Record<string, unknown>;
  status: 'running' | 'ok' | 'error' | 'denied';
  output?: string;
  error?: string;
}

export interface PlanStepDisplay {
  description: string;
  tool: string | null;
  done: boolean;
}

export interface ChatMessageDisplay {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
  streaming?: boolean;

  // metadados do assistente
  provider?: string;
  model?: string;
  toolCalls?: ToolCallDisplay[];
  plan?: PlanStepDisplay[];
  wasMultiIntent?: boolean;
  error?: string;
}
