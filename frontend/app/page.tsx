'use client';

import Link from "next/link";
import { Database, TrendingUp, Layers, BarChart3, MessageSquare, FolderKanban, ArrowRight } from "lucide-react";
import { useChatContext } from "@/components/chat";
import { useProject } from "@/lib/contexts";
import { cn } from "@/lib/utils";

interface QuickLinkProps {
  href: string;
  icon: React.ElementType;
  title: string;
  description: string;
  color: string;
}

function QuickLink({ href, icon: Icon, title, description, color }: QuickLinkProps) {
  return (
    <Link
      href={href}
      className="group flex items-start gap-4 p-4 rounded-xl bg-neutral-800/50 border border-neutral-700 hover:border-neutral-600 hover:bg-neutral-800 transition-all"
    >
      <div className={cn('p-3 rounded-lg', color)}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-white group-hover:text-purple-400 transition-colors">
          {title}
        </h3>
        <p className="text-sm text-neutral-400 mt-0.5">
          {description}
        </p>
      </div>
      <ArrowRight className="w-5 h-5 text-neutral-600 group-hover:text-neutral-400 transition-colors mt-1" />
    </Link>
  );
}

export default function HomePage() {
  const { openSidebar } = useChatContext();
  const { currentProject, projects } = useProject();

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Welcome Section */}
      <div className="text-center py-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          Welcome to Research Lab
        </h1>
        <p className="text-neutral-400">
          AI-powered trading strategy research and backtesting
        </p>
      </div>

      {/* Current Project Card */}
      {currentProject ? (
        <Link
          href={`/projects/${currentProject.id}`}
          className="block p-6 rounded-xl bg-gradient-to-r from-purple-900/30 to-blue-900/30 border border-purple-700/50 hover:border-purple-600 transition-all"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-purple-400 mb-1">Current Project</div>
              <h2 className="text-xl font-semibold text-white">{currentProject.name}</h2>
              {currentProject.thesis && (
                <p className="text-neutral-400 mt-1 line-clamp-1">{currentProject.thesis}</p>
              )}
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-2xl font-bold text-white">{currentProject.backtest_count}</div>
                <div className="text-xs text-neutral-500">backtests</div>
              </div>
              <ArrowRight className="w-6 h-6 text-purple-400" />
            </div>
          </div>
        </Link>
      ) : projects.length === 0 ? (
        <Link
          href="/projects/new"
          className="block p-6 rounded-xl bg-neutral-800/50 border-2 border-dashed border-neutral-600 hover:border-purple-500 hover:bg-neutral-800 transition-all text-center"
        >
          <FolderKanban className="w-10 h-10 text-neutral-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-white mb-1">Create Your First Project</h3>
          <p className="text-neutral-400 text-sm">
            Start organizing your research by creating a project
          </p>
        </Link>
      ) : (
        <Link
          href="/projects"
          className="block p-6 rounded-xl bg-neutral-800/50 border border-neutral-700 hover:border-purple-500 transition-all"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">Select a Project</h3>
              <p className="text-neutral-400 text-sm">
                You have {projects.length} project{projects.length !== 1 ? 's' : ''}
              </p>
            </div>
            <ArrowRight className="w-5 h-5 text-neutral-400" />
          </div>
        </Link>
      )}

      {/* Chat CTA */}
      <button
        onClick={openSidebar}
        className="w-full p-6 rounded-xl bg-gradient-to-r from-blue-900/30 to-cyan-900/30 border border-blue-700/50 hover:border-blue-600 transition-all text-left"
      >
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg bg-blue-600">
            <MessageSquare className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-white">Start Researching</h3>
            <p className="text-blue-300/70 text-sm">
              Chat with AI to design strategies, run backtests, and analyze results
            </p>
          </div>
          <div className="text-blue-400 text-sm font-medium">
            Open Chat &rarr;
          </div>
        </div>
      </button>

      {/* Quick Links Grid */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Quick Access</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <QuickLink
            href="/strategies"
            icon={Layers}
            title="Strategies"
            description="Browse and create trading strategies"
            color="bg-orange-600"
          />
          <QuickLink
            href="/data"
            icon={Database}
            title="Data"
            description="Manage historical market data"
            color="bg-blue-600"
          />
          <QuickLink
            href="/backtest"
            icon={TrendingUp}
            title="Backtest"
            description="Run strategy backtests"
            color="bg-green-600"
          />
          <QuickLink
            href="/results"
            icon={BarChart3}
            title="Results"
            description="View backtest reports"
            color="bg-purple-600"
          />
        </div>
      </div>
    </div>
  );
}
