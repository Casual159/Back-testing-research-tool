'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  Plus,
  Trash2,
  FileText,
  BarChart3,
  Layers,
  Bot,
  GripVertical,
  Check,
} from 'lucide-react';
import Link from 'next/link';
import { NotebookBlock } from '@/lib/contexts';
import { cn } from '@/lib/utils';

// =============================================================================
// Block Components
// =============================================================================

function TextBlock({
  block,
  onUpdate,
  onDelete,
}: {
  block: NotebookBlock;
  onUpdate: (content: string) => void;
  onDelete: () => void;
}) {
  const [isEditing, setIsEditing] = useState(!block.content);
  const [draft, setDraft] = useState(block.content);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      // Auto-resize
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [isEditing]);

  const handleSave = () => {
    onUpdate(draft);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setDraft(block.content);
      setIsEditing(false);
    }
  };

  const autoResize = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDraft(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = e.target.scrollHeight + 'px';
  };

  if (isEditing) {
    return (
      <div className="group relative">
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={autoResize}
          onKeyDown={handleKeyDown}
          onBlur={handleSave}
          placeholder="Write your notes..."
          rows={2}
          className="w-full px-4 py-3 bg-neutral-900 border border-purple-500/50 rounded-lg text-white placeholder-neutral-600 focus:outline-none focus:ring-1 focus:ring-purple-500 resize-none text-sm leading-relaxed"
        />
        <div className="flex items-center gap-1 mt-1 text-xs text-neutral-600">
          <span>Esc to cancel</span>
          <span>·</span>
          <button
            onMouseDown={(e) => { e.preventDefault(); handleSave(); }}
            className="text-purple-400 hover:text-purple-300"
          >
            Save
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="group relative cursor-text"
      onClick={() => setIsEditing(true)}
    >
      <div className="px-4 py-3 rounded-lg border border-transparent hover:border-neutral-700 transition-colors">
        {block.content ? (
          <p className="text-sm text-neutral-300 leading-relaxed whitespace-pre-wrap">
            {block.content}
          </p>
        ) : (
          <p className="text-sm text-neutral-600 italic">Empty note — click to edit</p>
        )}
      </div>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 text-neutral-600 hover:text-red-400 hover:bg-red-400/10 transition-all"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

function BacktestRefBlock({
  block,
  onDelete,
}: {
  block: NotebookBlock;
  onDelete: () => void;
}) {
  const meta = block.metadata || {};
  const returnPct = meta.total_return_pct as number | undefined;
  const sharpe = meta.sharpe_ratio as number | undefined;
  const trades = meta.total_trades as number | undefined;
  const strategy = meta.strategy_name as string | undefined;
  const symbol = meta.symbol as string | undefined;

  return (
    <div className="group relative">
      <Link
        href={meta.report_id ? `/results?id=${meta.report_id}` : '#'}
        className="block px-4 py-3 rounded-lg border border-blue-500/20 bg-blue-500/5 hover:border-blue-500/40 transition-colors"
      >
        <div className="flex items-center gap-2 mb-1">
          <BarChart3 className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium text-blue-300">
            {strategy || 'Backtest'} {symbol ? `on ${symbol}` : ''}
          </span>
        </div>
        {(returnPct !== undefined || sharpe !== undefined) && (
          <div className="flex items-center gap-4 text-xs text-neutral-400">
            {returnPct !== undefined && (
              <span className={returnPct >= 0 ? 'text-green-400' : 'text-red-400'}>
                Return: {returnPct >= 0 ? '+' : ''}{returnPct.toFixed(1)}%
              </span>
            )}
            {sharpe !== undefined && <span>Sharpe: {sharpe.toFixed(2)}</span>}
            {trades !== undefined && <span>Trades: {trades}</span>}
          </div>
        )}
        {block.content && (
          <p className="text-xs text-neutral-500 mt-1">{block.content}</p>
        )}
      </Link>
      <button
        onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDelete(); }}
        className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 text-neutral-600 hover:text-red-400 hover:bg-red-400/10 transition-all"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

function StrategyRefBlock({
  block,
  onDelete,
}: {
  block: NotebookBlock;
  onDelete: () => void;
}) {
  const meta = block.metadata || {};
  const strategyType = meta.strategy_type as string | undefined;

  return (
    <div className="group relative">
      <Link
        href={meta.strategy_name ? `/strategies` : '#'}
        className="block px-4 py-3 rounded-lg border border-purple-500/20 bg-purple-500/5 hover:border-purple-500/40 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium text-purple-300">
            {(meta.strategy_name as string) || 'Strategy'}
          </span>
          {strategyType && (
            <span className="text-xs text-neutral-500 bg-neutral-800 px-2 py-0.5 rounded">
              {strategyType}
            </span>
          )}
        </div>
        {block.content && (
          <p className="text-xs text-neutral-500 mt-1">{block.content}</p>
        )}
      </Link>
      <button
        onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDelete(); }}
        className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 text-neutral-600 hover:text-red-400 hover:bg-red-400/10 transition-all"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

function AgentNoteBlock({
  block,
  onDelete,
}: {
  block: NotebookBlock;
  onDelete: () => void;
}) {
  return (
    <div className="group relative">
      <div className="px-4 py-3 rounded-lg border border-amber-500/20 bg-amber-500/5">
        <div className="flex items-center gap-2 mb-1">
          <Bot className="w-4 h-4 text-amber-400" />
          <span className="text-xs font-medium text-amber-400/80 uppercase tracking-wider">Agent Insight</span>
        </div>
        <p className="text-sm text-neutral-300 leading-relaxed whitespace-pre-wrap">
          {block.content}
        </p>
      </div>
      <button
        onClick={onDelete}
        className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 text-neutral-600 hover:text-red-400 hover:bg-red-400/10 transition-all"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

// =============================================================================
// Add Block Menu
// =============================================================================

function AddBlockMenu({ onAdd }: { onAdd: (type: NotebookBlock['type']) => void }) {
  const [isOpen, setIsOpen] = useState(false);

  const options = [
    { type: 'text' as const, icon: FileText, label: 'Text Note', color: 'text-neutral-400' },
    { type: 'agent_note' as const, icon: Bot, label: 'Agent Note', color: 'text-amber-400' },
  ];

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-neutral-500 hover:text-purple-400 hover:bg-purple-400/10 rounded-lg transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add Block
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute left-0 top-full mt-1 z-20 bg-neutral-800 border border-neutral-700 rounded-lg shadow-xl py-1 min-w-[160px]">
            {options.map(({ type, icon: Icon, label, color }) => (
              <button
                key={type}
                onClick={() => { onAdd(type); setIsOpen(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-neutral-300 hover:bg-neutral-700 transition-colors"
              >
                <Icon className={cn('w-4 h-4', color)} />
                {label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// =============================================================================
// Main Notebook Component
// =============================================================================

interface NotebookProps {
  blocks: NotebookBlock[];
  onSave: (blocks: NotebookBlock[]) => Promise<void>;
}

export function Notebook({ blocks: initialBlocks, onSave }: NotebookProps) {
  const [blocks, setBlocks] = useState<NotebookBlock[]>(initialBlocks);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const saveTimeout = useRef<NodeJS.Timeout | null>(null);

  // Sync with parent when initialBlocks change (e.g. after refresh)
  useEffect(() => {
    setBlocks(initialBlocks);
  }, [initialBlocks]);

  const debouncedSave = useCallback((newBlocks: NotebookBlock[]) => {
    setDirty(true);
    if (saveTimeout.current) clearTimeout(saveTimeout.current);
    saveTimeout.current = setTimeout(async () => {
      setSaving(true);
      try {
        await onSave(newBlocks);
        setDirty(false);
      } catch (e) {
        console.error('Failed to save notebook:', e);
      } finally {
        setSaving(false);
      }
    }, 1000);
  }, [onSave]);

  const updateBlock = useCallback((id: string, content: string) => {
    setBlocks(prev => {
      const updated = prev.map(b => b.id === id ? { ...b, content } : b);
      debouncedSave(updated);
      return updated;
    });
  }, [debouncedSave]);

  const deleteBlock = useCallback((id: string) => {
    setBlocks(prev => {
      const updated = prev.filter(b => b.id !== id);
      debouncedSave(updated);
      return updated;
    });
  }, [debouncedSave]);

  const addBlock = useCallback((type: NotebookBlock['type']) => {
    const newBlock: NotebookBlock = {
      id: crypto.randomUUID(),
      type,
      content: '',
      created_at: new Date().toISOString(),
    };
    setBlocks(prev => {
      const updated = [...prev, newBlock];
      debouncedSave(updated);
      return updated;
    });
  }, [debouncedSave]);

  return (
    <div className="bg-neutral-800/50 rounded-xl border border-neutral-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">Notebook</h2>
          {saving && (
            <span className="text-xs text-neutral-500 animate-pulse">Saving...</span>
          )}
          {!saving && !dirty && blocks.length > 0 && (
            <span className="text-xs text-neutral-600 flex items-center gap-1">
              <Check className="w-3 h-3" /> Saved
            </span>
          )}
        </div>
        <AddBlockMenu onAdd={addBlock} />
      </div>

      {blocks.length === 0 ? (
        <div className="text-center py-8">
          <FileText className="w-10 h-10 text-neutral-600 mx-auto mb-2" />
          <p className="text-neutral-500">No notes yet</p>
          <p className="text-sm text-neutral-600">Add blocks to capture your research insights</p>
        </div>
      ) : (
        <div className="space-y-2">
          {blocks.map(block => {
            switch (block.type) {
              case 'text':
                return (
                  <TextBlock
                    key={block.id}
                    block={block}
                    onUpdate={(content) => updateBlock(block.id, content)}
                    onDelete={() => deleteBlock(block.id)}
                  />
                );
              case 'backtest_ref':
                return (
                  <BacktestRefBlock
                    key={block.id}
                    block={block}
                    onDelete={() => deleteBlock(block.id)}
                  />
                );
              case 'strategy_ref':
                return (
                  <StrategyRefBlock
                    key={block.id}
                    block={block}
                    onDelete={() => deleteBlock(block.id)}
                  />
                );
              case 'agent_note':
                return (
                  <AgentNoteBlock
                    key={block.id}
                    block={block}
                    onDelete={() => deleteBlock(block.id)}
                  />
                );
              default:
                return null;
            }
          })}
        </div>
      )}
    </div>
  );
}
