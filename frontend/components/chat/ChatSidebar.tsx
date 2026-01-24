'use client';

import { useRef, useEffect } from 'react';
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
    awaitingConfirmation,
    confirmationPrompt,
    currentPhase,
    totalCost,
    totalTokens,
    sendMessage,
    handleConfirm,
    handleCancel,
    startNewConversation,
    closeSidebar,
  } = useChatContext();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
        className={`fixed right-0 top-0 h-full w-full sm:w-[420px] bg-neutral-900 border-l border-neutral-800 shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
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
