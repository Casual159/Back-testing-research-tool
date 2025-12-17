'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { ToolCard } from './ToolCard';
import { MessageBlock, TextBlock } from './ChatProvider';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  blocks: MessageBlock[];
  timestamp?: Date;
  isStreaming?: boolean;
}

// Parse and render markdown content
function renderMarkdown(text: string): ReactNode[] {
  const lines = text.split('\n');
  const elements: ReactNode[] = [];
  let inCodeBlock = false;
  let codeBlockContent: string[] = [];

  const parseInlineFormatting = (text: string): ReactNode[] => {
    const parts: ReactNode[] = [];
    const regex = /(\*\*.*?\*\*|`[^`]+`)/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }

      const matched = match[0];
      if (matched.startsWith('**') && matched.endsWith('**')) {
        parts.push(<strong key={match.index} className="font-semibold text-white">{matched.slice(2, -2)}</strong>);
      } else if (matched.startsWith('`') && matched.endsWith('`')) {
        parts.push(
          <code key={match.index} className="px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-200 text-xs font-mono">
            {matched.slice(1, -1)}
          </code>
        );
      }

      lastIndex = match.index + matched.length;
    }

    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }

    return parts.length > 0 ? parts : [text];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.startsWith('```')) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeBlockContent = [];
      } else {
        elements.push(
          <pre key={`code-${i}`} className="my-2 p-3 rounded-lg bg-neutral-900 border border-neutral-800 overflow-x-auto">
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

    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={i} className="text-sm font-semibold mt-3 mb-1 text-white">
          {parseInlineFormatting(line.slice(4))}
        </h3>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h2 key={i} className="text-base font-semibold mt-3 mb-1.5 text-white">
          {parseInlineFormatting(line.slice(3))}
        </h2>
      );
    } else if (line.startsWith('# ')) {
      elements.push(
        <h1 key={i} className="text-lg font-bold mt-3 mb-2 text-white">
          {parseInlineFormatting(line.slice(2))}
        </h1>
      );
    } else if (line.match(/^[-*] /)) {
      elements.push(
        <div key={i} className="flex gap-2 my-0.5">
          <span className="text-neutral-600">-</span>
          <span>{parseInlineFormatting(line.slice(2))}</span>
        </div>
      );
    } else if (line.match(/^\d+\. /)) {
      const match = line.match(/^(\d+)\. (.*)$/);
      if (match) {
        elements.push(
          <div key={i} className="flex gap-2 my-0.5">
            <span className="text-neutral-500 min-w-[1.25rem]">{match[1]}.</span>
            <span>{parseInlineFormatting(match[2])}</span>
          </div>
        );
      }
    } else if (line.startsWith('|')) {
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
      if (isHeader) i++;
    } else if (line.startsWith('> ')) {
      elements.push(
        <div key={i} className="border-l-2 border-neutral-600 pl-3 my-1 text-neutral-400 italic">
          {parseInlineFormatting(line.slice(2))}
        </div>
      );
    } else if (!line.trim()) {
      elements.push(<div key={i} className="h-2" />);
    } else {
      elements.push(
        <p key={i} className="my-0.5 leading-relaxed">
          {parseInlineFormatting(line)}
        </p>
      );
    }
  }

  if (inCodeBlock && codeBlockContent.length > 0) {
    elements.push(
      <pre key="code-unclosed" className="my-2 p-3 rounded-lg bg-neutral-900 border border-neutral-800 overflow-x-auto">
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
  blocks,
  timestamp,
  isStreaming,
}: ChatMessageProps) {
  const isUser = role === 'user';

  // User message - bubble style
  if (isUser) {
    // Get text content from first text block
    const textContent = blocks.find((b): b is TextBlock => b.type === 'text')?.content || '';
    return (
      <div className="flex justify-end px-4 py-2">
        <div className="max-w-[85%] rounded-2xl rounded-br-md px-4 py-2.5 bg-blue-600 text-white text-sm">
          {textContent}
        </div>
      </div>
    );
  }

  // Assistant message - flat with vertical line, blocks rendered sequentially
  return (
    <div className="relative pl-4 pr-4 py-2">
      {/* Vertical line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-neutral-700" />

      {/* Content area - render blocks sequentially */}
      <div className="pl-4">
        {blocks.map((block, index) => {
          if (block.type === 'text') {
            return (
              <div key={index} className="text-sm text-neutral-300">
                {renderMarkdown(block.content)}
              </div>
            );
          }

          if (block.type === 'tool') {
            return (
              <ToolCard
                key={block.id}
                name={block.name}
                status={block.status}
                args={block.args}
                result={block.result}
                progress={block.progress}
              />
            );
          }

          return null;
        })}

        {/* Streaming cursor at the end */}
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-neutral-500 animate-pulse ml-0.5 align-middle rounded-sm" />
        )}

        {/* Timestamp */}
        {!isStreaming && timestamp && (
          <div className="mt-2 text-xs text-neutral-600">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </div>
  );
}
