'use client';

import { cn } from '@/lib/utils';

interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  timestamp: string;
}

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  phase?: string;
  timestamp?: Date;
}

export function ChatMessage({ role, content, toolCalls, phase, timestamp }: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <div className={cn('flex gap-3 p-4', isUser ? 'justify-end' : 'justify-start')}>
      {/* Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-md bg-neutral-700 flex items-center justify-center text-neutral-300 text-xs font-medium">
          A
        </div>
      )}

      <div className={cn('max-w-[80%] space-y-2', isUser ? 'items-end' : 'items-start')}>
        {/* Phase badge */}
        {phase && !isUser && (
          <span className="text-xs px-1.5 py-0.5 rounded bg-neutral-700 text-neutral-400">
            {phase.replace('_', ' ')}
          </span>
        )}

        {/* Message bubble */}
        <div
          className={cn(
            'rounded-md px-3 py-2 text-sm',
            isUser
              ? 'bg-neutral-600 text-neutral-100'
              : 'bg-neutral-800 text-neutral-200 border border-neutral-700'
          )}
        >
          {/* Render markdown-like content */}
          <div className="prose prose-invert prose-sm max-w-none">
            {content.split('\n').map((line, i) => {
              // Headers
              if (line.startsWith('### ')) {
                return <h3 key={i} className="text-base font-semibold mt-3 mb-1">{line.slice(4)}</h3>;
              }
              if (line.startsWith('## ')) {
                return <h2 key={i} className="text-lg font-semibold mt-4 mb-2">{line.slice(3)}</h2>;
              }
              // List items
              if (line.startsWith('- ')) {
                return <li key={i} className="ml-4">{line.slice(2)}</li>;
              }
              // Bold text
              if (line.includes('**')) {
                const parts = line.split(/\*\*(.*?)\*\*/g);
                return (
                  <p key={i} className="my-1">
                    {parts.map((part, j) =>
                      j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                    )}
                  </p>
                );
              }
              // Tables (basic)
              if (line.startsWith('|')) {
                return <code key={i} className="block text-xs">{line}</code>;
              }
              // Regular paragraph
              if (line.trim()) {
                return <p key={i} className="my-1">{line}</p>;
              }
              return <br key={i} />;
            })}
          </div>
        </div>

        {/* Tool calls */}
        {toolCalls && toolCalls.length > 0 && (
          <div className="space-y-1">
            {toolCalls.map((tc, i) => (
              <div
                key={i}
                className="text-xs bg-neutral-900 border border-neutral-700 rounded px-2 py-1 flex items-center gap-2"
              >
                <span className="text-neutral-500">{tc.tool_name}</span>
              </div>
            ))}
          </div>
        )}

        {/* Timestamp */}
        {timestamp && (
          <span className="text-xs text-neutral-500">
            {timestamp.toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* User avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-md bg-neutral-600 flex items-center justify-center text-neutral-200 text-xs font-medium">
          U
        </div>
      )}
    </div>
  );
}
