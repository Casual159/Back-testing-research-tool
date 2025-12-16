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
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={closeSidebar}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed right-0 top-0 h-full w-full sm:w-[420px] bg-gray-950 border-l border-gray-800 z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="border-b border-gray-800 px-4 py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={closeSidebar}
              className="p-1 hover:bg-gray-800 rounded text-gray-400 hover:text-white"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            <h2 className="font-semibold text-white">Research Agent</h2>
            <span
              className={`text-xs px-2 py-0.5 rounded ${phaseColors[currentPhase] || 'bg-gray-700'}`}
            >
              {currentPhase.replace('_', ' ')}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">
              {totalTokens > 0 && `${(totalTokens / 1000).toFixed(1)}k`}
              {totalCost > 0 && ` · $${totalCost.toFixed(3)}`}
            </span>
            <button
              onClick={startNewConversation}
              className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300"
            >
              New
            </button>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-6 py-8">
              <div className="text-4xl mb-3">📊</div>
              <h3 className="text-lg font-semibold mb-2 text-white">Research Agent</h3>
              <p className="text-gray-400 text-sm mb-4">
                Design strategies, run backtests, and analyze results.
              </p>
              <div className="grid gap-2 w-full text-sm">
                <button
                  onClick={() => sendMessage("What strategies are available?")}
                  className="px-3 py-2 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700 text-left text-gray-300"
                >
                  What strategies are available?
                </button>
                <button
                  onClick={() => sendMessage("What's the current market regime for BTCUSDT?")}
                  className="px-3 py-2 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700 text-left text-gray-300"
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
                  content={message.content}
                  toolCalls={message.toolCalls}
                  activeTools={message.activeTools}
                  phase={message.phase}
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
        <div className="shrink-0 border-t border-gray-800">
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
