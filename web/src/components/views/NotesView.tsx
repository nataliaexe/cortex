import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { StickyNote, Plus, Search, Trash2 } from 'lucide-react';
import { fetchNotes, createNote, deleteNote, type Note } from '@/lib/api';
import { cn } from '@/lib/utils';
import { useToast } from '@/components/ui/Toast';

export function NotesView() {
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const qc = useQueryClient();

  const notesQ = useQuery({
    queryKey: ['notes', search],
    queryFn: () => fetchNotes({ search: search || undefined, limit: 100 }),
  });

  const toast = useToast();
  const deleteM = useMutation({
    mutationFn: (id: string) => deleteNote(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notes'] });
      toast.push({ kind: 'success', title: 'Nota removida' });
    },
    onError: (e: Error) => toast.push({ kind: 'error', title: 'Erro ao remover', description: e.message }),
  });

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-bg-border px-4 py-2">
        <div className="relative flex-1 max-w-md">
          <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-fg-dim" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar notas..."
            className="input pl-7"
          />
        </div>
        <div className="ml-auto">
          <button onClick={() => setShowForm(!showForm)} className="btn-primary text-xs">
            <Plus size={12} />
            <span>Nova nota</span>
          </button>
        </div>
      </div>

      {showForm && (
        <NewNoteForm
          onClose={() => setShowForm(false)}
          onCreated={() => qc.invalidateQueries({ queryKey: ['notes'] })}
        />
      )}

      <div className="flex-1 overflow-y-auto">
        {notesQ.isLoading && <div className="p-8 text-center text-sm text-fg-dim">Carregando...</div>}
        {notesQ.data && notesQ.data.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <StickyNote size={24} className="mb-2 text-fg-dim" />
            <div className="text-sm text-fg-muted">
              {search ? 'Nenhuma nota encontrada' : 'Nenhuma nota ainda'}
            </div>
          </div>
        )}
        {notesQ.data && notesQ.data.length > 0 && (
          <div className="mx-auto grid max-w-5xl grid-cols-1 gap-3 p-4 md:grid-cols-2 lg:grid-cols-3">
            {notesQ.data.map((n) => (
              <NoteCard key={n.id} note={n} onDelete={() => deleteM.mutate(n.id)} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function NoteCard({ note, onDelete }: { note: Note; onDelete: () => void }) {
  const [confirming, setConfirming] = useState(false);
  const tags = note.tags?.split(',').filter(Boolean) || [];

  return (
    <div className="group flex flex-col rounded border border-bg-border bg-bg-panel p-3 transition-colors hover:border-accent/40">
      <div className="flex items-start justify-between gap-2">
        <h3 className="flex-1 text-sm font-medium text-fg-base line-clamp-2">
          {note.title || '(sem titulo)'}
        </h3>
        <div className="opacity-0 transition-opacity group-hover:opacity-100">
          {confirming ? (
            <div className="flex gap-1">
              <button
                onClick={onDelete}
                className="rounded bg-state-danger/20 px-1.5 py-0.5 text-2xs text-state-danger"
              >
                OK
              </button>
              <button
                onClick={() => setConfirming(false)}
                className="rounded px-1.5 py-0.5 text-2xs text-fg-dim"
              >
                X
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirming(true)}
              className="text-fg-dim hover:text-state-danger"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>
      </div>
      <p className="mt-2 flex-1 text-xs text-fg-muted line-clamp-4 whitespace-pre-wrap">
        {note.content}
      </p>
      {tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {tags.map((t) => (
            <span key={t} className="badge-muted">{t}</span>
          ))}
        </div>
      )}
      <div className="mt-2 text-2xs text-fg-dim">
        {new Date(note.created_at).toLocaleString('pt-BR', {
          day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
        })}
      </div>
    </div>
  );
}

function NewNoteForm({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [tagsStr, setTagsStr] = useState('');

  const m = useMutation({
    mutationFn: () => createNote({
      content,
      title: title || undefined,
      tags: tagsStr ? tagsStr.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
    }),
    onSuccess: () => {
      onCreated();
      onClose();
    },
  });

  return (
    <div className="border-b border-bg-border bg-bg-elevated p-3">
      <div className="mx-auto max-w-3xl space-y-2">
        <input
          className="input"
          placeholder="Titulo (opcional)"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          className="input min-h-[100px] resize-y"
          placeholder="Conteudo da nota..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
          autoFocus
        />
        <input
          className="input"
          placeholder="Tags (separadas por virgula)"
          value={tagsStr}
          onChange={(e) => setTagsStr(e.target.value)}
        />
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn-ghost text-xs">Cancelar</button>
          <button
            onClick={() => m.mutate()}
            disabled={!content || m.isPending}
            className="btn-primary text-xs disabled:opacity-40"
          >
            {m.isPending ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  );
}
