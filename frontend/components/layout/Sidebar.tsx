'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  FolderKanban,
  Layers,
  Database,
  PlayCircle,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Beaker,
  Plus,
  ChevronDown,
  LogOut,
  User
} from 'lucide-react';
import { useProject, useAuth } from '@/lib/contexts';
import { cn } from '@/lib/utils';
import { config } from '@/lib/config';

const API_BASE_URL = config.apiUrl;

const SIDEBAR_COLLAPSED_KEY = 'sidebar_collapsed';

interface NavItemProps {
  href: string;
  icon: React.ElementType;
  label: string;
  isCollapsed: boolean;
  isActive: boolean;
}

function NavItem({ href, icon: Icon, label, isCollapsed, isActive }: NavItemProps) {
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200',
        'hover:bg-neutral-800 group',
        isActive && 'bg-neutral-800 text-white',
        !isActive && 'text-neutral-400 hover:text-white'
      )}
    >
      <Icon className={cn('w-5 h-5 flex-shrink-0', isActive && 'text-purple-400')} />
      {!isCollapsed && (
        <span className="text-sm font-medium truncate">{label}</span>
      )}
    </Link>
  );
}

interface ProjectSelectorProps {
  isCollapsed: boolean;
}

function ProjectSelector({ isCollapsed }: ProjectSelectorProps) {
  const { currentProject, projects, selectProject } = useProject();
  const [isOpen, setIsOpen] = useState(false);

  if (isCollapsed) {
    return (
      <div className="px-2 py-2">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 transition-colors"
          title={currentProject?.name || 'Select Project'}
        >
          <FolderKanban className="w-5 h-5 text-purple-400 mx-auto" />
        </button>
      </div>
    );
  }

  return (
    <div className="px-3 py-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'w-full flex items-center justify-between px-3 py-2 rounded-lg',
          'bg-neutral-800 hover:bg-neutral-700 transition-colors',
          'text-sm font-medium'
        )}
      >
        <div className="flex items-center gap-2 min-w-0">
          <FolderKanban className="w-4 h-4 text-purple-400 flex-shrink-0" />
          <span className="truncate">
            {currentProject?.name || 'Select Project'}
          </span>
        </div>
        <ChevronDown className={cn(
          'w-4 h-4 text-neutral-500 transition-transform',
          isOpen && 'rotate-180'
        )} />
      </button>

      {isOpen && (
        <div className="mt-2 py-1 bg-neutral-800 rounded-lg border border-neutral-700 max-h-64 overflow-y-auto">
          {projects.length === 0 ? (
            <div className="px-3 py-2 text-sm text-neutral-500">
              No projects yet
            </div>
          ) : (
            projects.map(project => (
              <button
                key={project.id}
                onClick={() => {
                  selectProject(project.id);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full text-left px-3 py-2 text-sm hover:bg-neutral-700 transition-colors',
                  currentProject?.id === project.id && 'bg-neutral-700 text-purple-400'
                )}
              >
                <div className="truncate">{project.name}</div>
                <div className="text-xs text-neutral-500 truncate">
                  {project.status}
                  {project.backtest_count > 0 && ` · ${project.backtest_count} backtests`}
                </div>
              </button>
            ))
          )}

          <Link
            href="/projects/new"
            className="flex items-center gap-2 px-3 py-2 text-sm text-purple-400 hover:bg-neutral-700 border-t border-neutral-700 mt-1"
            onClick={() => setIsOpen(false)}
          >
            <Plus className="w-4 h-4" />
            New Project
          </Link>
        </div>
      )}
    </div>
  );
}

function SystemStatus() {
  const [status, setStatus] = useState<'ok' | 'warning' | 'error'>('ok');

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/data/stats`);
        setStatus(response.ok ? 'ok' : 'error');
      } catch {
        setStatus('error');
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const statusColors = {
    ok: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500'
  };

  return (
    <div className="flex items-center gap-2 px-3 py-2 text-xs text-neutral-500">
      <div className={cn('w-2 h-2 rounded-full', statusColors[status])} />
      <span>System {status === 'ok' ? 'OK' : status}</span>
    </div>
  );
}

function UserSection({ isCollapsed }: { isCollapsed: boolean }) {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-neutral-800 transition-colors group">
      {user.image ? (
        <img
          src={user.image}
          alt={user.name || 'User'}
          className="w-7 h-7 rounded-full flex-shrink-0"
          referrerPolicy="no-referrer"
        />
      ) : (
        <div className="w-7 h-7 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4 text-white" />
        </div>
      )}
      {!isCollapsed && (
        <>
          <span className="text-sm text-neutral-300 truncate flex-1">
            {user.name || user.email}
          </span>
          <button
            onClick={logout}
            className="p-1 rounded hover:bg-neutral-700 text-neutral-500 hover:text-white transition-colors"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </>
      )}
    </div>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Load collapsed state from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
    if (stored === 'true') {
      setIsCollapsed(true);
    }
  }, []);

  const toggleCollapsed = () => {
    const newValue = !isCollapsed;
    setIsCollapsed(newValue);
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(newValue));
  };

  const navItems = [
    { href: '/projects', icon: FolderKanban, label: 'Projects' },
    { href: '/strategies', icon: Layers, label: 'Strategies' },
    { href: '/data', icon: Database, label: 'Data' },
    { href: '/backtest', icon: PlayCircle, label: 'Backtest' },
    { href: '/results', icon: BarChart3, label: 'Results' },
  ];

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-full z-40',
        'bg-neutral-900 border-r border-neutral-800',
        'flex flex-col transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Header */}
      <div className={cn(
        'flex items-center justify-between h-14 px-3 border-b border-neutral-800',
        isCollapsed && 'justify-center'
      )}>
        {!isCollapsed && (
          <Link href="/" className="flex items-center gap-2">
            <Beaker className="w-6 h-6 text-purple-400" />
            <span className="font-semibold text-white">Research Lab</span>
          </Link>
        )}
        {isCollapsed && (
          <Link href="/">
            <Beaker className="w-6 h-6 text-purple-400" />
          </Link>
        )}
        <button
          onClick={toggleCollapsed}
          className={cn(
            'p-1.5 rounded-lg hover:bg-neutral-800 text-neutral-400 hover:text-white transition-colors',
            isCollapsed && 'absolute -right-3 top-4 bg-neutral-900 border border-neutral-800'
          )}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Project Selector */}
      <ProjectSelector isCollapsed={isCollapsed} />

      {/* Divider */}
      <div className="mx-3 border-t border-neutral-800" />

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-1 overflow-y-auto">
        {navItems.map(item => (
          <NavItem
            key={item.href}
            {...item}
            isCollapsed={isCollapsed}
            isActive={pathname === item.href || pathname.startsWith(item.href + '/')}
          />
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-neutral-800 py-2 px-2 space-y-1">
        <NavItem
          href="/settings"
          icon={Settings}
          label="Settings"
          isCollapsed={isCollapsed}
          isActive={pathname === '/settings'}
        />
        {!isCollapsed && <SystemStatus />}
        <UserSection isCollapsed={isCollapsed} />
      </div>
    </aside>
  );
}
