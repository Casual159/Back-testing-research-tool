'use client';

import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  timestamp: string;
  result?: Record<string, unknown>;
  success?: boolean;
}

interface ActiveTool {
  name: string;
  args: Record<string, unknown>;
  status: 'running' | 'completed' | 'error';
  result?: Record<string, unknown>;
  progress?: {
    current: number;
    total: number;
    pct: number;
  };
}

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  activeTools?: ActiveTool[];
  phase?: string;
  timestamp?: Date;
  isStreaming?: boolean;
}

// Tool display names
const TOOL_INFO: Record<string, { label: string; icon: string }> = {
  list_strategies: { label: 'Loading strategies', icon: '📋' },
  get_strategy: { label: 'Getting strategy', icon: '🔍' },
  check_data: { label: 'Checking data', icon: '📊' },
  get_market_regime: { label: 'Analyzing regime', icon: '📈' },
  get_data_stats: { label: 'Getting stats', icon: '📁' },
  fetch_data: { label: 'Fetching data', icon: '⬇️' },
  create_strategy: { label: 'Creating strategy', icon: '✨' },
  run_backtest: { label: 'Running backtest', icon: '⚡' },
  save_report: { label: 'Saving report', icon: '💾' },
  suggest_enhancement: { label: 'Recording suggestion', icon: '💡' },
};

function formatToolResult(toolName: string, result: Record<string, unknown>): string {
  if (result.error) {
    return String(result.error);
  }
  switch (toolName) {
    case 'run_backtest':
      return `${result.total_return}% | Sharpe ${result.sharpe_ratio}`;
    case 'list_strategies':
      return `${result.count} strategies`;
    case 'check_data':
      return result.available ? 'Available' : 'No data';
    case 'fetch_data':
      return result.success ? `${result.candles} candles` : 'Failed';
    case 'create_strategy':
      return result.success ? 'Created' : 'Failed';
    default:
      return 'Done';
  }
}

// Inline tool badge component
function ToolBadge({
  tool,
  status,
  result,
  progress
}: {
  tool: string;
  status: 'running' | 'completed' | 'error';
  result?: Record<string, unknown>;
  progress?: {
    current: number;
    total: number;
    pct: number;
  };
}) {
  const info = TOOL_INFO[tool] || { label: tool, icon: '🔧' };
  const isError = status === 'error' || (result && 'error' in result);
  const hasProgress = status === 'running' && progress && progress.total > 0;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono my-0.5 relative overflow-hidden',
        status === 'running' && 'bg-blue-950/50 text-blue-300 border border-blue-800',
        status === 'completed' && !isError && 'bg-neutral-800/80 text-neutral-400 border border-neutral-700',
        isError && 'bg-red-950/50 text-red-400 border border-red-800'
      )}
    >
      {/* Progress bar background */}
      {hasProgress && (
        <span
          className="absolute inset-0 bg-blue-600/30 transition-all duration-200"
          style={{ width: `${progress.pct}%` }}
        />
      )}
      <span className="relative opacity-75">{info.icon}</span>
      <span className="relative">{info.label}</span>
      {status === 'running' && !hasProgress && (
        <span className="relative w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
      )}
      {hasProgress && (
        <span className="relative text-blue-200">
          {progress.pct}%
        </span>
      )}
      {status === 'completed' && result && (
        <span className="opacity-60">
          {formatToolResult(tool, result)}
        </span>
      )}
    </span>
  );
}

// Parse and render markdown content
function renderMarkdown(text: string): ReactNode[] {
  const lines = text.split('\n');
  const elements: ReactNode[] = [];
  let inCodeBlock = false;
  let codeBlockContent: string[] = [];

  const parseInlineFormatting = (text: string): ReactNode[] => {
    const parts: ReactNode[] = [];
    // Match bold, inline code, and regular text
    const regex = /(\*\*.*?\*\*|`[^`]+`)/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
      // Add text before match
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }

      const matched = match[0];
      if (matched.startsWith('**') && matched.endsWith('**')) {
        // Bold
        parts.push(<strong key={match.index}>{matched.slice(2, -2)}</strong>);
      } else if (matched.startsWith('`') && matched.endsWith('`')) {
        // Inline code
        parts.push(
          <code key={match.index} className="px-1 py-0.5 rounded bg-neutral-700 text-neutral-200 text-xs font-mono">
            {matched.slice(1, -1)}
          </code>
        );
      }

      lastIndex = match.index + matched.length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return parts.length > 0 ? parts : [text];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block handling
    if (line.startsWith('```')) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeBlockContent = [];
      } else {
        // End code block
        elements.push(
          <pre key={`code-${i}`} className="my-2 p-3 rounded bg-neutral-900 border border-neutral-700 overflow-x-auto">
            <code className="text-xs font-mono text-neutral-300">
              {codeBlockContent.join('\n')}
            </code>
          </pre>
        );
        inCodeBlock = false;
        codeBlockContent = [];
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line);
      continue;
    }

    // Headers
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={i} className="text-sm font-semibold mt-3 mb-1 text-neutral-100">
          {parseInlineFormatting(line.slice(4))}
        </h3>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h2 key={i} className="text-base font-semibold mt-3 mb-1.5 text-neutral-100">
          {parseInlineFormatting(line.slice(3))}
        </h2>
      );
    } else if (line.startsWith('# ')) {
      elements.push(
        <h1 key={i} className="text-lg font-bold mt-3 mb-2 text-neutral-100">
          {parseInlineFormatting(line.slice(2))}
        </h1>
      );
    }
    // Unordered list
    else if (line.match(/^[-*] /)) {
      elements.push(
        <div key={i} className="flex gap-2 my-0.5 ml-2">
          <span className="text-neutral-500">•</span>
          <span>{parseInlineFormatting(line.slice(2))}</span>
        </div>
      );
    }
    // Numbered list
    else if (line.match(/^\d+\. /)) {
      const match = line.match(/^(\d+)\. (.*)$/);
      if (match) {
        elements.push(
          <div key={i} className="flex gap-2 my-0.5 ml-2">
            <span className="text-neutral-500 min-w-[1.25rem]">{match[1]}.</span>
            <span>{parseInlineFormatting(match[2])}</span>
          </div>
        );
      }
    }
    // Table row
    else if (line.startsWith('|')) {
      const cells = line.split('|').filter(c => c.trim());
      const isHeader = lines[i + 1]?.match(/^\|[-:| ]+\|$/);
      elements.push(
        <div key={i} className={cn(
          "font-mono text-xs flex gap-2 py-0.5",
          isHeader && "font-semibold border-b border-neutral-700"
        )}>
          {cells.map((cell, j) => (
            <span key={j} className="flex-1">{cell.trim()}</span>
          ))}
        </div>
      );
      // Skip separator line
      if (isHeader) i++;
    }
    // Blockquote
    else if (line.startsWith('> ')) {
      elements.push(
        <div key={i} className="border-l-2 border-neutral-600 pl-3 my-1 text-neutral-400 italic">
          {parseInlineFormatting(line.slice(2))}
        </div>
      );
    }
    // Empty line
    else if (!line.trim()) {
      elements.push(<div key={i} className="h-2" />);
    }
    // Regular paragraph
    else {
      elements.push(
        <p key={i} className="my-0.5">
          {parseInlineFormatting(line)}
        </p>
      );
    }
  }

  // Handle unclosed code block
  if (inCodeBlock && codeBlockContent.length > 0) {
    elements.push(
      <pre key="code-unclosed" className="my-2 p-3 rounded bg-neutral-900 border border-neutral-700 overflow-x-auto">
        <code className="text-xs font-mono text-neutral-300">
          {codeBlockContent.join('\n')}
        </code>
      </pre>
    );
  }

  return elements;
}

export function ChatMessage({
  role,
  content,
  toolCalls,
  activeTools,
  phase,
  timestamp,
  isStreaming,
}: ChatMessageProps) {
  const isUser = role === 'user';
  const hasTools = (activeTools && activeTools.length > 0) || (toolCalls && toolCalls.length > 0);

  return (
    <div className={cn('flex gap-3 p-4', isUser ? 'justify-end' : 'justify-start')}>
      {/* Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-md bg-neutral-700 flex items-center justify-center text-neutral-300 text-xs font-medium">
          A
        </div>
      )}

      <div className={cn('max-w-[85%] space-y-1.5', isUser ? 'items-end' : 'items-start')}>
        {/* Message content */}
        {(content || isStreaming || !hasTools) && (
          <div
            className={cn(
              'rounded-lg px-3 py-2 text-sm leading-relaxed',
              isUser
                ? 'bg-blue-600 text-white'
                : 'bg-neutral-800 text-neutral-200 border border-neutral-700'
            )}
          >
            {content ? renderMarkdown(content) : null}
            {/* Streaming cursor */}
            {isStreaming && (
              <span className="inline-block w-2 h-4 bg-neutral-400 animate-pulse ml-0.5 align-middle" />
            )}
          </div>
        )}

        {/* Tool calls - inline style */}
        {activeTools && activeTools.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {activeTools.map((tool, i) => (
              <ToolBadge
                key={i}
                tool={tool.name}
                status={tool.status}
                result={tool.result}
                progress={tool.progress}
              />
            ))}
          </div>
        )}

        {/* Completed tool calls (after streaming) */}
        {!isStreaming && !activeTools?.length && toolCalls && toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {toolCalls.map((tc, i) => (
              <ToolBadge
                key={i}
                tool={tc.tool_name}
                status={tc.success === false ? 'error' : 'completed'}
                result={tc.result}
              />
            ))}
          </div>
        )}

        {/* Timestamp & Phase */}
        {!isStreaming && (timestamp || phase) && (
          <div className="flex items-center gap-2 text-xs text-neutral-500">
            {phase && (
              <span className="px-1.5 py-0.5 rounded bg-neutral-800 border border-neutral-700">
                {phase.replace(/_/g, ' ')}
              </span>
            )}
            {timestamp && <span>{timestamp.toLocaleTimeString()}</span>}
          </div>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-white text-xs font-medium">
          U
        </div>
      )}
    </div>
  );
}
