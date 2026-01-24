'use client';

import Link from 'next/link';
import { MoreVertical, Play, Pause, CheckCircle2, XCircle, HelpCircle } from 'lucide-react';
import { Project } from '@/lib/contexts';
import { cn } from '@/lib/utils';

interface ProjectCardProps {
  project: Project;
  isActive?: boolean;
  onSelect?: () => void;
}

const statusIcons = {
  active: Play,
  paused: Pause,
  concluded: CheckCircle2,
};

const statusColors = {
  active: 'text-green-400 bg-green-400/10',
  paused: 'text-yellow-400 bg-yellow-400/10',
  concluded: 'text-neutral-400 bg-neutral-400/10',
};

const validationIcons = {
  validated: CheckCircle2,
  invalidated: XCircle,
  inconclusive: HelpCircle,
};

const validationColors = {
  validated: 'text-green-400',
  invalidated: 'text-red-400',
  inconclusive: 'text-yellow-400',
};

export function ProjectCard({ project, isActive, onSelect }: ProjectCardProps) {
  const StatusIcon = statusIcons[project.status];
  const ValidationIcon = project.validation_result ? validationIcons[project.validation_result] : null;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <Link
      href={`/projects/${project.id}`}
      onClick={onSelect}
      className={cn(
        'block p-4 rounded-xl border-2 transition-all duration-200',
        'hover:border-purple-500/50 hover:bg-neutral-800/50',
        isActive
          ? 'border-purple-500 bg-purple-500/10'
          : 'border-neutral-700 bg-neutral-800/30'
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-white truncate">{project.name}</h3>
            <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1', statusColors[project.status])}>
              <StatusIcon className="w-3 h-3" />
              {project.status}
            </span>
          </div>

          {project.thesis && (
            <p className="mt-1 text-sm text-neutral-400 line-clamp-2">
              {project.thesis}
            </p>
          )}

          <div className="mt-3 flex items-center gap-4 text-xs text-neutral-500">
            <span>{project.backtest_count} backtests</span>
            <span>{project.conversation_count} conversations</span>
            <span>Updated {formatDate(project.updated_at)}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {ValidationIcon && (
            <ValidationIcon className={cn('w-5 h-5', validationColors[project.validation_result!])} />
          )}
          <button
            onClick={(e) => {
              e.preventDefault();
              // TODO: Open context menu
            }}
            className="p-1 rounded hover:bg-neutral-700 text-neutral-400 hover:text-white transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>
    </Link>
  );
}
