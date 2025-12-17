'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, ExternalLink, Play } from 'lucide-react';

interface ToolCardProps {
  name: string;
  status: 'running' | 'completed' | 'error';
  args?: Record<string, unknown>;
  result?: Record<string, unknown>;
  duration?: number;
  progress?: {
    current: number;
    total: number;
    pct: number;
  };
}

// Tool metadata
const TOOL_META: Record<string, { label: string; icon: string; color: string }> = {
  list_strategies: { label: 'List Strategies', icon: '📋', color: 'blue' },
  get_strategy: { label: 'Get Strategy', icon: '🔍', color: 'blue' },
  check_data: { label: 'Check Data', icon: '📊', color: 'cyan' },
  get_market_regime: { label: 'Market Regime', icon: '📈', color: 'purple' },
  get_data_stats: { label: 'Data Stats', icon: '📁', color: 'cyan' },
  fetch_data: { label: 'Fetch Data', icon: '⬇️', color: 'green' },
  create_strategy: { label: 'Create Strategy', icon: '✨', color: 'yellow' },
  run_backtest: { label: 'Run Backtest', icon: '⚡', color: 'orange' },
  save_report: { label: 'Save Report', icon: '💾', color: 'green' },
  suggest_enhancement: { label: 'Suggestion', icon: '💡', color: 'yellow' },
  list_reports: { label: 'List Reports', icon: '📑', color: 'purple' },
  get_report: { label: 'Get Report', icon: '📄', color: 'purple' },
};

const colorClasses: Record<string, { border: string; bg: string; text: string }> = {
  blue: { border: 'border-blue-700', bg: 'bg-blue-950/30', text: 'text-blue-400' },
  cyan: { border: 'border-cyan-700', bg: 'bg-cyan-950/30', text: 'text-cyan-400' },
  purple: { border: 'border-purple-700', bg: 'bg-purple-950/30', text: 'text-purple-400' },
  green: { border: 'border-green-700', bg: 'bg-green-950/30', text: 'text-green-400' },
  yellow: { border: 'border-yellow-700', bg: 'bg-yellow-950/30', text: 'text-yellow-400' },
  orange: { border: 'border-orange-700', bg: 'bg-orange-950/30', text: 'text-orange-400' },
  red: { border: 'border-red-700', bg: 'bg-red-950/30', text: 'text-red-400' },
};

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return value.toLocaleString();
    return value.toFixed(2);
  }
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function formatResultSummary(toolName: string, result: Record<string, unknown>): string {
  if (result.error) return String(result.error);

  switch (toolName) {
    case 'run_backtest':
      const ret = result.total_return ?? result.total_return_pct;
      const sharpe = result.sharpe_ratio;
      const trades = result.total_trades;
      return `${ret}% return | Sharpe ${sharpe} | ${trades} trades`;
    case 'list_strategies':
      // Handle both {count: N} and {strategies: [...]}
      const count = result.count ?? (result.strategies as unknown[])?.length ?? (result.names as unknown[])?.length;
      return `${count} strategies found`;
    case 'check_data':
      if (!result.available) return 'No data available';
      const candles = result.candle_count ?? result.count ?? result.candles;
      return candles ? `Available: ${candles} candles` : 'Data available';
    case 'fetch_data':
      const fetched = result.candles ?? result.count ?? result.candle_count;
      return result.success !== false ? `Fetched ${fetched} candles` : 'Failed to fetch';
    case 'create_strategy':
      return result.name ? `Created: ${result.name}` : (result.success ? 'Strategy created' : 'Creation failed');
    case 'get_market_regime':
      const regime = result.regime ?? result.simplified_regime ?? result.current_regime;
      return regime ? String(regime) : 'Regime analyzed';
    case 'get_data_stats':
      // Handle various response formats
      const stats = result.stats ?? result.data ?? result.symbols;
      if (Array.isArray(stats)) return `${stats.length} datasets`;
      if (typeof result.count === 'number') return `${result.count} datasets`;
      return 'Stats retrieved';
    case 'save_report':
      return result.report_id ? 'Report saved' : (result.success ? 'Report saved' : 'Save failed');
    case 'get_strategy':
      return result.name ? String(result.name) : 'Strategy loaded';
    case 'get_report':
      const strat = result.strategy ?? result.strategy_name;
      return strat ? `${strat}` : 'Report loaded';
    case 'list_reports':
      const reportCount = result.count ?? (result.reports as unknown[])?.length;
      return `${reportCount} reports`;
    default:
      return 'Completed';
  }
}

export function ToolCard({ name, status, args, result, duration, progress }: ToolCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const meta = TOOL_META[name] || { label: name, icon: '🔧', color: 'blue' };
  const colors = status === 'error' ? colorClasses.red : colorClasses[meta.color];
  const isError = status === 'error' || (result && 'error' in result);

  const hasDetails = (args && Object.keys(args).length > 0) || (result && Object.keys(result).length > 0);

  return (
    <div
      className={cn(
        'rounded-lg border overflow-hidden transition-all my-2',
        colors.border,
        colors.bg
      )}
    >
      {/* Header - always visible */}
      <button
        onClick={() => hasDetails && setIsExpanded(!isExpanded)}
        disabled={!hasDetails}
        className={cn(
          'w-full px-3 py-2 flex items-center gap-2 text-left',
          hasDetails && 'hover:bg-white/5 cursor-pointer'
        )}
      >
        {/* Expand icon */}
        {hasDetails ? (
          isExpanded ? (
            <ChevronDown className="w-4 h-4 text-neutral-500 shrink-0" />
          ) : (
            <ChevronRight className="w-4 h-4 text-neutral-500 shrink-0" />
          )
        ) : (
          <div className="w-4" />
        )}

        {/* Icon */}
        <span className="text-base">{meta.icon}</span>

        {/* Label */}
        <span className={cn('font-medium text-sm', colors.text)}>
          {meta.label}
        </span>

        {/* Status indicator */}
        <div className="flex-1 flex items-center justify-end gap-2">
          {status === 'running' && (
            <>
              {progress && progress.total > 0 ? (
                <span className="text-xs text-neutral-400">{progress.pct}%</span>
              ) : (
                <span className="flex items-center gap-1.5 text-xs text-neutral-400">
                  <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
                  Running
                </span>
              )}
            </>
          )}

          {status === 'completed' && !isError && (
            <span className="text-xs text-neutral-400">
              {result && formatResultSummary(name, result)}
            </span>
          )}

          {isError && (
            <span className="text-xs text-red-400">Error</span>
          )}

          {duration && (
            <span className="text-xs text-neutral-500">{(duration / 1000).toFixed(1)}s</span>
          )}

          {/* Status icon */}
          {status === 'running' && (
            <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          )}
          {status === 'completed' && !isError && (
            <svg className="w-4 h-4 text-green-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          )}
          {isError && (
            <svg className="w-4 h-4 text-red-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          )}
        </div>
      </button>

      {/* Progress bar */}
      {status === 'running' && progress && progress.total > 0 && (
        <div className="h-1 bg-neutral-800">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${progress.pct}%` }}
          />
        </div>
      )}

      {/* Expanded details */}
      {isExpanded && hasDetails && (
        <div className="border-t border-neutral-700/50 px-3 py-2 space-y-3 text-sm">
          {/* Parameters */}
          {args && Object.keys(args).length > 0 && (
            <div>
              <div className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                Parameters
              </div>
              <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
                {Object.entries(args).map(([key, value]) => (
                  <div key={key} className="contents">
                    <span className="text-neutral-500">{key}</span>
                    <span className="text-neutral-300 font-mono text-xs">
                      {formatValue(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Results */}
          {result && Object.keys(result).length > 0 && !('error' in result) && (
            <div>
              <div className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                Results
              </div>
              <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
                {Object.entries(result)
                  .filter(([key]) => !['success', 'error'].includes(key))
                  .slice(0, 8) // Limit displayed results
                  .map(([key, value]) => (
                    <div key={key} className="contents">
                      <span className="text-neutral-500">{key.replace(/_/g, ' ')}</span>
                      <span className="text-neutral-300 font-mono text-xs">
                        {formatValue(value)}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Error */}
          {result && 'error' in result && (
            <div className="text-red-400 text-xs font-mono bg-red-950/30 rounded p-2">
              {String(result.error)}
            </div>
          )}

          {/* Actions */}
          {status === 'completed' && name === 'run_backtest' && result && !('error' in result) && (
            <div className="flex gap-2 pt-1">
              <button className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors">
                <ExternalLink className="w-3.5 h-3.5" />
                View Full Report
              </button>
              <button className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-neutral-300 transition-colors">
                <Play className="w-3.5 h-3.5" />
                Run Again
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
