import { useState, useEffect } from 'react';
import { StickyNote, Plus, Trash2, Edit2, Check, X } from 'lucide-react';
import { notesApi } from '../lib/api-service';
import type { Note } from '../types';
import { Button, Textarea, EmptyState } from './ui';

interface NotesProps {
  projectId?: number;
  paperId?: number;
  experimentId?: number;
  experimentRunId?: number;
}

export default function Notes({ projectId, paperId, experimentId, experimentRunId }: NotesProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState('');
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');
  const [showForm, setShowForm] = useState(false);

  const fetchNotes = async () => {
    try {
      const data = await notesApi.list({
        project_id: projectId,
        paper_id: paperId,
        experiment_id: experimentId,
        experiment_run_id: experimentRunId,
      });
      setNotes(data);
    } catch (error) {
      console.error('Failed to fetch notes:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, [projectId, paperId, experimentId, experimentRunId]);

  const handleCreate = async () => {
    if (!newNote.trim()) return;
    setCreating(true);
    try {
      await notesApi.create({
        content: newNote,
        project_id: projectId,
        paper_id: paperId,
        experiment_id: experimentId,
        experiment_run_id: experimentRunId,
      });
      setNewNote('');
      setShowForm(false);
      fetchNotes();
    } catch (error) {
      console.error('Failed to create note:', error);
    } finally {
      setCreating(false);
    }
  };

  const handleUpdate = async (id: number) => {
    if (!editContent.trim()) return;
    try {
      await notesApi.update(id, { content: editContent });
      setEditingId(null);
      fetchNotes();
    } catch (error) {
      console.error('Failed to update note:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this note?')) return;
    try {
      await notesApi.delete(id);
      fetchNotes();
    } catch (error) {
      console.error('Failed to delete note:', error);
    }
  };

  const startEdit = (note: Note) => {
    setEditingId(note.id);
    setEditContent(note.content);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Notes</h3>
        {!showForm && (
          <Button
            variant="secondary"
            size="sm"
            icon={<Plus className="w-4 h-4" />}
            onClick={() => setShowForm(true)}
          >
            Add Note
          </Button>
        )}
      </div>

      {showForm && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <Textarea
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Write your note here..."
            rows={3}
          />
          <div className="flex gap-2 justify-end">
            <Button variant="ghost" size="sm" onClick={() => { setShowForm(false); setNewNote(''); }}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleCreate} loading={creating}>
              Save Note
            </Button>
          </div>
        </div>
      )}

      {notes.length === 0 && !showForm ? (
        <EmptyState
          icon={<StickyNote className="w-8 h-8" />}
          title="No notes yet"
          description="Add notes to keep track of your thoughts and observations."
        />
      ) : (
        <div className="space-y-3">
          {notes.map((note) => (
            <div
              key={note.id}
              className="bg-white border border-gray-200 rounded-lg p-4 group"
            >
              {editingId === note.id ? (
                <div className="space-y-3">
                  <Textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={3}
                  />
                  <div className="flex gap-2 justify-end">
                    <Button
                      variant="ghost"
                      size="sm"
                      icon={<X className="w-4 h-4" />}
                      onClick={() => setEditingId(null)}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      icon={<Check className="w-4 h-4" />}
                      onClick={() => handleUpdate(note.id)}
                    >
                      Save
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <p className="text-gray-700 whitespace-pre-wrap">{note.content}</p>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                    <span className="text-xs text-gray-400">
                      {new Date(note.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => startEdit(note)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(note.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
