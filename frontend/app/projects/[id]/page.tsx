'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  CheckCircle2,
  Pencil,
  Trash2,
  MessageSquare,
  Layers,
  PlayCircle,
  Flag,
  Plus
} from 'lucide-react';
import { useProject, Project, NotebookBlock, ResearchEvent, useOnboarding } from '@/lib/contexts';
import { useChatContext } from '@/components/chat/ChatProvider';
import { Notebook } from '@/components/projects/Notebook';
import { cn } from '@/lib/utils';

const eventIcons: Record<string, React.ElementType> = {
  strategy_created: Layers,
  backtest_run: PlayCircle,
  conclusion: CheckCircle2,
  note: MessageSquare,
  milestone: Flag,
};

const eventColors: Record<string, string> = {
  strategy_created: 'bg-purple-500',
  backtest_run: 'bg-blue-500',
  conclusion: 'bg-green-500',
  note: 'bg-neutral-500',
  milestone: 'bg-yellow-500',
};

function TimelineNode({ event }: { event: ResearchEvent }) {
  const Icon = eventIcons[event.event_type] || MessageSquare;

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  return (
    <div className="flex gap-4 group">
      {/* Timeline dot */}
      <div className="flex flex-col items-center">
        <div className={cn('w-8 h-8 rounded-full flex items-center justify-center', eventColors[event.event_type])}>
          <Icon className="w-4 h-4 text-white" />
        </div>
        <div className="w-0.5 flex-1 bg-neutral-700 group-last:hidden" />
      </div>

      {/* Content */}
      <div className="flex-1 pb-6">
        <div className="bg-neutral-800/50 rounded-lg p-4 border border-neutral-700 hover:border-neutral-600 transition-colors">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h4 className="font-medium text-white">{event.title}</h4>
              {event.summary && (
                <p className="text-sm text-neutral-400 mt-1">{event.summary}</p>
              )}
            </div>
            <span className="text-xs text-neutral-500 whitespace-nowrap">
              {formatTime(event.created_at)}
            </span>
          </div>

          {/* Reference link */}
          {event.reference_type && event.reference_id && (
            <Link
              href={
                event.reference_type === 'backtest_report'
                  ? `/results?id=${event.reference_id}`
                  : event.reference_type === 'strategy'
                    ? `/strategies/${event.reference_id}`
                    : '#'
              }
              className="inline-flex items-center gap-1 mt-2 text-xs text-purple-400 hover:text-purple-300"
            >
              View {event.reference_type.replace('_', ' ')}
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const {
    projects,
    currentProject,
    selectProject,
    updateProject,
    deleteProject,
    events,
    eventsLoading,
    createEvent
  } = useProject();

  const { openSidebar, sendMessage } = useChatContext();
  const { preferences } = useOnboarding();

  const [project, setProject] = useState<Project | null>(null);
  const [notebookBlocks, setNotebookBlocks] = useState<NotebookBlock[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editedThesis, setEditedThesis] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [showAddNote, setShowAddNote] = useState(false);
  const [noteTitle, setNoteTitle] = useState('');
  const [noteSummary, setNoteSummary] = useState('');

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Load project from list (basic data)
  useEffect(() => {
    const found = projects.find(p => p.id === projectId);
    if (found) {
      setProject(found);
      setEditedThesis(found.thesis || '');
      selectProject(found.id);
    }
  }, [projectId, projects, selectProject]);

  // Fetch full project detail (with notebook) separately
  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}`);
        if (res.ok) {
          const data = await res.json();
          setNotebookBlocks(data.notebook || []);
        }
      } catch (e) {
        console.error('Failed to fetch project detail:', e);
      }
    };
    fetchDetail();
  }, [projectId, API_BASE_URL]);

  const handleSaveNotebook = useCallback(async (blocks: NotebookBlock[]) => {
    await updateProject(projectId, { notebook: blocks });
    setNotebookBlocks(blocks);
  }, [projectId, updateProject]);

  const handleThesisSave = async () => {
    if (!project) return;
    await updateProject(project.id, { thesis: editedThesis });
    setIsEditing(false);
  };

  const handleDelete = async () => {
    if (!project) return;
    if (!confirm('Are you sure you want to delete this project? This cannot be undone.')) return;

    setIsDeleting(true);
    try {
      await deleteProject(project.id);
      router.push('/projects');
    } catch (error) {
      console.error('Failed to delete project:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleStartResearch = () => {
    openSidebar();
    if (project?.thesis) {
      sendMessage(`I want to research: ${project.thesis}`);
    }
  };

  const handleAddNote = async () => {
    if (!noteTitle.trim()) return;
    await createEvent({
      event_type: 'note',
      title: noteTitle,
      summary: noteSummary || undefined,
    });
    setNoteTitle('');
    setNoteSummary('');
    setShowAddNote(false);
  };

  if (!project) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <Link
            href="/projects"
            className="inline-flex items-center gap-2 text-neutral-400 hover:text-white transition-colors mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            All Projects
          </Link>
          <h1 className="text-2xl font-bold text-white">{project.name}</h1>
          {project.description && (
            <p className="text-neutral-400 mt-1">{project.description}</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleStartResearch}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            Start Research
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-2 text-neutral-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Research Context - Full Width */}
      <div className="bg-gradient-to-br from-purple-900/20 to-neutral-900 rounded-xl border border-purple-500/20 p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <span className="text-xs font-medium text-purple-400 uppercase tracking-wider">Research Hypothesis</span>
            <h2 className="text-xl font-semibold text-white mt-1">
              {project.thesis || 'Define your research question'}
            </h2>
          </div>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="p-2 text-neutral-400 hover:text-white rounded-lg hover:bg-neutral-800 transition-colors"
          >
            <Pencil className="w-4 h-4" />
          </button>
        </div>

        {isEditing && (
          <div className="space-y-3 mt-4 pt-4 border-t border-purple-500/20">
            <textarea
              value={editedThesis}
              onChange={(e) => setEditedThesis(e.target.value)}
              placeholder="What trading idea are you researching?"
              rows={3}
              className="w-full px-4 py-3 bg-neutral-900 border border-neutral-600 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setIsEditing(false)}
                className="px-3 py-1.5 text-neutral-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleThesisSave}
                className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg"
              >
                Save
              </button>
            </div>
          </div>
        )}

        {/* User Context from Onboarding */}
        {preferences && (
          <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-purple-500/20">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-neutral-800 text-neutral-300 border border-neutral-700">
              {preferences.experience_level === 'beginner' && '🌱 Beginner'}
              {preferences.experience_level === 'intermediate' && '📈 Intermediate'}
              {preferences.experience_level === 'advanced' && '🎯 Advanced'}
              {preferences.experience_level === 'professional' && '💼 Professional'}
            </span>
            {preferences.goals.map((goal, i) => (
              <span
                key={i}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-neutral-800 text-neutral-400 border border-neutral-700"
              >
                {goal}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Notebook */}
      <Notebook blocks={notebookBlocks} onSave={handleSaveNotebook} />

      {/* Timeline - Full Width */}
      <div>
          <div className="bg-neutral-800/50 rounded-xl border border-neutral-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Research Log</h2>
              <button
                onClick={() => setShowAddNote(!showAddNote)}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-purple-400 hover:text-purple-300 hover:bg-purple-400/10 rounded-lg transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Note
              </button>
            </div>

            {/* Add note form */}
            {showAddNote && (
              <div className="mb-6 p-4 bg-neutral-900 rounded-lg border border-neutral-600 space-y-3">
                <input
                  type="text"
                  value={noteTitle}
                  onChange={(e) => setNoteTitle(e.target.value)}
                  placeholder="Note title..."
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <textarea
                  value={noteSummary}
                  onChange={(e) => setNoteSummary(e.target.value)}
                  placeholder="Details (optional)..."
                  rows={2}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowAddNote(false)}
                    className="px-3 py-1.5 text-neutral-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddNote}
                    disabled={!noteTitle.trim()}
                    className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Add
                  </button>
                </div>
              </div>
            )}

            {eventsLoading ? (
              <div className="flex justify-center py-8">
                <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : events.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquare className="w-10 h-10 text-neutral-600 mx-auto mb-2" />
                <p className="text-neutral-500">No events yet</p>
                <p className="text-sm text-neutral-600">Start researching to see activity here</p>
              </div>
            ) : (
              <div>
                {events.map(event => (
                  <TimelineNode key={event.id} event={event} />
                ))}
              </div>
            )}
          </div>
      </div>
    </div>
  );
}
