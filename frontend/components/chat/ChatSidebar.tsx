'use client';

import { useRef, useEffect, useCallback, useState } from 'react';
import { config } from '@/lib/config';
import { useChatContext } from './ChatProvider';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { ConfirmationCard } from './ConfirmationCard';

const phaseColors: Record<string, string> = {
  STRATEGY_DESIGN: 'bg-purple-600',
  STRATEGY_VALIDATION: 'bg-yellow-600',
  DATA_SELECTION: 'bg-blue-600',
  BACKTEST_EXECUTION: 'bg-orange-600',
  RESULTS_ANALYSIS: 'bg-green-600',
  COMPLETE: 'bg-gray-600',
  CONVERSATION: 'bg-gray-700',
};

export function ChatSidebar() {
  const {
    messages,
    isLoading,
    isOpen,
    chatWidth,
    setChatWidth,
    awaitingConfirmation,
    confirmationPrompt,
    currentPhase,
    totalCost,
    totalTokens,
    creditBalance,
    conversationHistory,
    sendMessage,
    handleConfirm,
    handleCancel,
    startNewConversation,
    loadConversation,
    closeSidebar,
  } = useChatContext();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const dragStartX = useRef(0);
  const dragStartWidth = useRef(0);
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    const check = () => setIsDesktop(window.innerWidth >= 640);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    isDragging.current = true;
    dragStartX.current = e.clientX;
    dragStartWidth.current = chatWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [chatWidth]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return;
      const delta = dragStartX.current - e.clientX;
      setChatWidth(dragStartWidth.current + delta);
    };

    const handleMouseUp = () => {
      if (isDragging.current) {
        isDragging.current = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [setChatWidth]);

  return (
    <>
      {/* Overlay for mobile only */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 sm:hidden"
          onClick={closeSidebar}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed right-0 top-0 h-full w-full bg-neutral-900 border-l border-neutral-800 shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={isDesktop ? { width: `${chatWidth}px` } : undefined}
      >
        {/* Drag handle */}
        <div
          onMouseDown={handleMouseDown}
          className="absolute left-0 top-0 bottom-0 w-1.5 cursor-col-resize hover:bg-purple-500/50 transition-colors hidden sm:block z-10"
        />

        {/* Header - h-14 to match sidebar header */}
        <div className="h-14 border-b border-neutral-800 px-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={closeSidebar}
              className="p-1.5 hover:bg-neutral-700 rounded-md text-neutral-400 hover:text-white transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            <h2 className="font-semibold text-white">Research Agent</h2>
            <span
              className={`text-xs px-2 py-0.5 rounded-md text-white/90 ${phaseColors[currentPhase] || 'bg-neutral-600'}`}
            >
              {currentPhase.replace('_', ' ')}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {config.billingEnabled && creditBalance !== null && (
              <span className={`text-xs font-medium ${
                creditBalance > 2 ? 'text-green-400' : creditBalance > 0.5 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                ${creditBalance.toFixed(2)}
              </span>
            )}
            <span className="text-xs text-neutral-500">
              {totalTokens > 0 && `${(totalTokens / 1000).toFixed(1)}k`}
              {totalCost > 0 && ` · $${totalCost.toFixed(3)}`}
            </span>
            <button
              onClick={startNewConversation}
              className="text-xs px-3 py-1.5 rounded-md bg-neutral-700 hover:bg-neutral-600 text-neutral-300 transition-colors"
            >
              New
            </button>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-6 py-8">
              <div className="w-12 h-12 rounded-lg bg-neutral-800 flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-400">
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
              </div>
              <h3 className="text-base font-medium mb-1 text-white">Research Agent</h3>
              <p className="text-neutral-500 text-sm mb-6">
                Design strategies, run backtests, and analyze results.
              </p>
              <div className="grid gap-2 w-full text-sm">
                <button
                  onClick={() => sendMessage("What strategies are available?")}
                  className="px-4 py-2.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-left text-neutral-400 hover:text-neutral-300 transition-colors"
                >
                  What strategies are available?
                </button>
                <button
                  onClick={() => sendMessage("What's the current market regime for BTCUSDT?")}
                  className="px-4 py-2.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-left text-neutral-400 hover:text-neutral-300 transition-colors"
                >
                  Current market regime?
                </button>
              </div>

              {/* Past conversations */}
              {conversationHistory.length > 0 && (
                <div className="w-full mt-6 border-t border-neutral-800 pt-4">
                  <h4 className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2 px-1">Recent Conversations</h4>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {conversationHistory.map((conv) => (
                      <button
                        key={conv.id}
                        onClick={() => loadConversation(conv.id)}
                        className="w-full px-3 py-2 rounded-lg bg-neutral-800/50 hover:bg-neutral-700/50 text-left transition-colors group"
                      >
                        <p className="text-sm text-neutral-300 truncate group-hover:text-white">
                          {conv.preview || 'Conversation'}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs text-neutral-600">
                            {conv.message_count} msgs
                          </span>
                          {conv.updated_at && (
                            <span className="text-xs text-neutral-600">
                              {new Date(conv.updated_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="py-2">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  role={message.role}
                  blocks={message.blocks}
                  timestamp={message.timestamp}
                  isStreaming={message.isStreaming}
                />
              ))}

              {/* Confirmation card */}
              {awaitingConfirmation && confirmationPrompt && (
                <ConfirmationCard
                  prompt={confirmationPrompt}
                  onConfirm={handleConfirm}
                  onCancel={handleCancel}
                  disabled={isLoading}
                />
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Low balance warning */}
        {config.billingEnabled && creditBalance !== null && creditBalance < 0.5 && creditBalance > 0 && (
          <div className="shrink-0 px-4 py-2 bg-yellow-900/20 border-t border-yellow-700/50 text-yellow-400 text-xs">
            Low balance (${creditBalance.toFixed(2)}) — top up in Settings to avoid interruption.
          </div>
        )}
        {config.billingEnabled && creditBalance !== null && creditBalance <= 0 && (
          <div className="shrink-0 px-4 py-2 bg-red-900/20 border-t border-red-700/50 text-red-400 text-xs">
            No credits remaining. Top up in Settings to continue using the agent.
          </div>
        )}

        {/* Input area */}
        <div className="shrink-0 border-t border-neutral-800">
          <ChatInput
            onSend={sendMessage}
            disabled={isLoading}
            placeholder="Ask about strategies..."
          />
        </div>
      </div>
    </>
  );
}
