'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useChatContext } from '@/components/chat';
import {
  FlaskConical,
  MessageSquare,
  Link as LinkIcon,
  Image as ImageIcon,
  Clock,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ChevronRight
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

type SessionStatus = 'captured' | 'exploring' | 'testing' | 'concluded';
type ValidationResult = 'validated' | 'invalidated' | 'inconclusive';

interface ResearchSession {
  id: string;
  title: string;
  originalInput: string;
  status: SessionStatus;
  validationResult?: ValidationResult;
  thesisSummary?: string;
  situationCount: number;
  batchCount: number;
  activeBatchProgress?: number;
  createdAt: Date;
  updatedAt: Date;
}

interface BatchJob {
  id: string;
  name: string;
  sessionId: string;
  progress: number;
  totalTests: number;
  completedTests: number;
  status: 'queued' | 'running' | 'completed';
  estimatedMinutes?: number;
}

// =============================================================================
// Mock Data
// =============================================================================

const MOCK_SESSIONS: ResearchSession[] = [
  {
    id: '1',
    title: 'RSI reversal in range markets',
    originalInput: 'Does RSI < 30 lead to bounce in ranging markets?',
    status: 'exploring',
    thesisSummary: 'RSI oversold conditions in RANGE regime produce mean-reversion opportunities',
    situationCount: 2,
    batchCount: 1,
    activeBatchProgress: undefined,
    createdAt: new Date(Date.now() - 1000 * 60 * 45), // 45 min ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 15), // 15 min ago
  },
  {
    id: '2',
    title: 'Post-halving momentum effect',
    originalInput: 'Slyšel jsem v podcastu, že po halvingu Bitcoin vždycky roste 12 měsíců',
    status: 'testing',
    thesisSummary: 'BTC shows statistically significant growth 0-12 months after halving',
    situationCount: 1,
    batchCount: 1,
    activeBatchProgress: 67,
    createdAt: new Date(Date.now() - 1000 * 60 * 120), // 2h ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 2), // 2 min ago
  },
  {
    id: '3',
    title: 'MA crossover parameter optimization',
    originalInput: 'What are the optimal MA crossover parameters for trending markets?',
    status: 'concluded',
    validationResult: 'validated',
    thesisSummary: 'EMA(8,30) on 4h timeframe shows consistent performance in TREND_UP regime',
    situationCount: 1,
    batchCount: 3,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 26), // yesterday
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
  },
  {
    id: '4',
    title: 'BTC dumps after FOMC announcements',
    originalInput: 'Someone on Twitter said BTC always dumps after FOMC meetings',
    status: 'concluded',
    validationResult: 'invalidated',
    thesisSummary: 'No statistically significant correlation between FOMC dates and BTC price drops',
    situationCount: 1,
    batchCount: 1,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 28),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 25),
  },
  {
    id: '5',
    title: 'Bollinger squeeze breakout strategy',
    originalInput: 'Bollinger Band squeezes predict explosive moves',
    status: 'captured',
    situationCount: 0,
    batchCount: 0,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 72), // 3 days ago
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 72),
  },
];

const MOCK_ACTIVE_BATCHES: BatchJob[] = [
  {
    id: 'b1',
    name: 'Post-halving MA parameter sweep',
    sessionId: '2',
    progress: 67,
    totalTests: 90,
    completedTests: 60,
    status: 'running',
    estimatedMinutes: 4,
  },
  {
    id: 'b2',
    name: 'MTF analysis comparison',
    sessionId: '1',
    progress: 0,
    totalTests: 120,
    completedTests: 0,
    status: 'queued',
  },
];

// =============================================================================
// Helper Functions
// =============================================================================

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 172800) return 'yesterday';
  return `${Math.floor(seconds / 86400)} days ago`;
}

function getTimeGroup(date: Date): string {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  const weekAgo = new Date(today.getTime() - 7 * 86400000);

  if (date >= today) return 'TODAY';
  if (date >= yesterday) return 'YESTERDAY';
  if (date >= weekAgo) return 'THIS WEEK';
  return 'EARLIER';
}

function groupSessionsByTime(sessions: ResearchSession[]): Record<string, ResearchSession[]> {
  const groups: Record<string, ResearchSession[]> = {};

  for (const session of sessions) {
    const group = getTimeGroup(session.updatedAt);
    if (!groups[group]) groups[group] = [];
    groups[group].push(session);
  }

  return groups;
}

// =============================================================================
// Components
// =============================================================================

function StatusBadge({ status, validationResult }: { status: SessionStatus; validationResult?: ValidationResult }) {
  const config = {
    captured: { label: 'CAPTURED', className: 'bg-gray-700 text-gray-300' },
    exploring: { label: 'EXPLORING', className: 'bg-blue-900 text-blue-300' },
    testing: { label: 'TESTING', className: 'bg-yellow-900 text-yellow-300' },
    concluded: {
      validated: { label: 'VALIDATED', className: 'bg-green-900 text-green-300', icon: CheckCircle2 },
      invalidated: { label: 'INVALIDATED', className: 'bg-red-900 text-red-300', icon: XCircle },
      inconclusive: { label: 'INCONCLUSIVE', className: 'bg-gray-700 text-gray-300', icon: HelpCircle },
    },
  };

  if (status === 'concluded' && validationResult) {
    const c = config.concluded[validationResult];
    const Icon = c.icon;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${c.className}`}>
        <Icon className="w-3 h-3" />
        {c.label}
      </span>
    );
  }

  const c = config[status] as { label: string; className: string };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${c.className}`}>
      {c.label}
    </span>
  );
}

function NewResearchCard({ onExplore }: { onExplore: (text: string) => void }) {
  const [inputText, setInputText] = useState('');

  const handleExplore = () => {
    if (inputText.trim()) {
      onExplore(inputText.trim());
      setInputText('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleExplore();
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
      <div className="flex items-center gap-2 mb-4">
        <FlaskConical className="w-5 h-5 text-purple-400" />
        <h2 className="font-semibold">New Research</h2>
      </div>

      <p className="text-sm text-gray-400 mb-3">What&apos;s on your mind?</p>

      <textarea
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Start typing a thesis, question, or idea..."
        className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm resize-none focus:outline-none focus:border-purple-500 transition-colors"
        rows={3}
      />

      <div className="flex items-center justify-between mt-3">
        <div className="flex gap-2">
          <button
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded transition-colors"
            title="Paste URL (coming soon)"
          >
            <LinkIcon className="w-3.5 h-3.5" />
            Paste URL
          </button>
          <button
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded transition-colors"
            title="Upload image (coming soon)"
          >
            <ImageIcon className="w-3.5 h-3.5" />
            Upload
          </button>
        </div>

        <button
          onClick={handleExplore}
          disabled={!inputText.trim()}
          className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 rounded transition-colors"
        >
          Explore
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function ActiveWorkCard({ batches }: { batches: BatchJob[] }) {
  const runningBatches = batches.filter(b => b.status === 'running' || b.status === 'queued');

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-yellow-400" />
          <h2 className="font-semibold">Active Work</h2>
        </div>
        {runningBatches.length > 0 && (
          <span className="px-2 py-0.5 text-xs font-medium bg-yellow-900 text-yellow-300 rounded">
            {runningBatches.length}
          </span>
        )}
      </div>

      {runningBatches.length === 0 ? (
        <div className="text-center py-6">
          <p className="text-sm text-gray-500">No batch tests running</p>
          <p className="text-xs text-gray-600 mt-1">
            When you run batch tests, they&apos;ll appear here
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {runningBatches.map((batch) => (
            <div key={batch.id} className="bg-gray-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium truncate pr-2">{batch.name}</span>
                <button className="text-xs text-gray-400 hover:text-white">View</button>
              </div>

              <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden mb-2">
                <div
                  className={`h-full transition-all duration-500 ${
                    batch.status === 'running' ? 'bg-yellow-500' : 'bg-gray-600'
                  }`}
                  style={{ width: `${batch.progress}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>
                  {batch.status === 'queued'
                    ? 'Queued'
                    : `${batch.completedTests}/${batch.totalTests} tests`
                  }
                </span>
                {batch.status === 'running' && batch.estimatedMinutes && (
                  <span>~{batch.estimatedMinutes} min left</span>
                )}
                {batch.status === 'queued' && (
                  <span>starts after current</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SessionCard({ session, onClick }: { session: ResearchSession; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 rounded-lg bg-gray-900 border border-gray-800 hover:border-gray-700 transition-colors"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3 className="font-medium text-sm">{session.title}</h3>
        <StatusBadge status={session.status} validationResult={session.validationResult} />
      </div>

      {session.thesisSummary && (
        <p className="text-xs text-gray-400 mb-2 line-clamp-2">
          {session.thesisSummary}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>
          {session.situationCount > 0
            ? `${session.situationCount} situation${session.situationCount > 1 ? 's' : ''}`
            : 'No situations yet'
          }
          {session.batchCount > 0 && ` · ${session.batchCount} batch${session.batchCount > 1 ? 'es' : ''}`}
          {session.activeBatchProgress !== undefined && (
            <span className="text-yellow-400"> · {session.activeBatchProgress}% running</span>
          )}
        </span>
        <span>{formatTimeAgo(session.updatedAt)}</span>
      </div>
    </button>
  );
}

function ResearchLog({
  sessions,
  onSessionClick
}: {
  sessions: ResearchSession[];
  onSessionClick: (session: ResearchSession) => void;
}) {
  const groupedSessions = groupSessionsByTime(sessions);
  const groupOrder = ['TODAY', 'YESTERDAY', 'THIS WEEK', 'EARLIER'];

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold">Research Log</h2>
        <select className="text-xs bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-400">
          <option>All</option>
          <option>Captured</option>
          <option>Testing</option>
          <option>Concluded</option>
        </select>
      </div>

      {sessions.length === 0 ? (
        <div className="text-center py-12">
          <FlaskConical className="w-12 h-12 text-gray-700 mx-auto mb-3" />
          <h3 className="font-medium mb-1">No research sessions yet</h3>
          <p className="text-sm text-gray-500">
            Start by typing a thesis, question, or idea above.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {groupOrder.map((group) => {
            const groupSessions = groupedSessions[group];
            if (!groupSessions || groupSessions.length === 0) return null;

            return (
              <div key={group}>
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-2 h-2 rounded-full bg-gray-600" />
                  <span className="text-xs font-medium text-gray-500">{group}</span>
                  <div className="flex-1 h-px bg-gray-800" />
                </div>

                <div className="space-y-2 pl-4 border-l border-gray-800">
                  {groupSessions.map((session) => (
                    <SessionCard
                      key={session.id}
                      session={session}
                      onClick={() => onSessionClick(session)}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main Page
// =============================================================================

export default function ResearchPage() {
  const { openSidebar, sendMessage } = useChatContext();
  const [sessions] = useState<ResearchSession[]>(MOCK_SESSIONS);
  const [activeBatches] = useState<BatchJob[]>(MOCK_ACTIVE_BATCHES);

  const handleExplore = (text: string) => {
    openSidebar();
    // Small delay to ensure sidebar is open before sending
    setTimeout(() => {
      sendMessage(`I want to explore this idea: "${text}"`);
    }, 100);
  };

  const handleSessionClick = (session: ResearchSession) => {
    // TODO: Navigate to session detail or open in chat
    console.log('Session clicked:', session.id);
    openSidebar();
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-gray-400 hover:text-white">
              &larr; Home
            </Link>
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-purple-400" />
              Research Lab
            </h1>
          </div>
          <button
            onClick={openSidebar}
            className="flex items-center gap-2 text-sm px-4 py-2 rounded bg-gray-800 hover:bg-gray-700 transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            Open Chat
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto p-6">
        {/* Top Section: New Research + Active Work */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-1">
            <NewResearchCard onExplore={handleExplore} />
          </div>
          <div className="lg:col-span-2">
            <ActiveWorkCard batches={activeBatches} />
          </div>
        </div>

        {/* Research Log */}
        <ResearchLog
          sessions={sessions}
          onSessionClick={handleSessionClick}
        />
      </div>
    </div>
  );
}
