'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { ChatMessage, ChatInput, ConfirmationCard } from '@/components/chat';

interface ToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  timestamp: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  phase?: string;
  timestamp: Date;
}

interface AgentResponse {
  message: string;
  conversation_id: string;
  phase: string;
  awaiting_confirmation: boolean;
  confirmation_prompt: string | null;
  data: Record<string, unknown>;
  tool_calls: ToolCall[];
  tokens_used: number;
  cost_usd: number;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [confirmationPrompt, setConfirmationPrompt] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState<string>('CONVERSATION');
  const [totalCost, setTotalCost] = useState(0);
  const [totalTokens, setTotalTokens] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setAwaitingConfirmation(false);

    try {
      const response = await fetch('http://localhost:8000/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data: AgentResponse = await response.json();

      // Update conversation state
      setConversationId(data.conversation_id);
      setCurrentPhase(data.phase);
      setTotalCost((prev) => prev + data.cost_usd);
      setTotalTokens((prev) => prev + data.tokens_used);

      // Add assistant message
      const assistantMessage: Message = {
        id: Date.now().toString() + '-assistant',
        role: 'assistant',
        content: data.message,
        toolCalls: data.tool_calls,
        phase: data.phase,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Handle confirmation
      if (data.awaiting_confirmation && data.confirmation_prompt) {
        setAwaitingConfirmation(true);
        setConfirmationPrompt(data.confirmation_prompt);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: Date.now().toString() + '-error',
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}. Make sure the API server is running.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = () => {
    sendMessage('Yes, proceed');
  };

  const handleCancel = () => {
    sendMessage("No, let me reconsider");
  };

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setCurrentPhase('CONVERSATION');
    setAwaitingConfirmation(false);
    setConfirmationPrompt(null);
    setTotalCost(0);
    setTotalTokens(0);
  };

  // Phase to color mapping
  const phaseColors: Record<string, string> = {
    STRATEGY_DESIGN: 'bg-purple-600',
    STRATEGY_VALIDATION: 'bg-yellow-600',
    DATA_SELECTION: 'bg-blue-600',
    BACKTEST_EXECUTION: 'bg-orange-600',
    RESULTS_ANALYSIS: 'bg-green-600',
    COMPLETE: 'bg-gray-600',
    CONVERSATION: 'bg-gray-700',
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-gray-400 hover:text-white">
              &larr; Back
            </Link>
            <h1 className="text-xl font-semibold">Research Agent</h1>
            <span
              className={`text-xs px-2 py-1 rounded ${phaseColors[currentPhase] || 'bg-gray-700'}`}
            >
              {currentPhase.replace('_', ' ')}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-gray-400">
              {totalTokens.toLocaleString()} tokens | ${totalCost.toFixed(4)}
            </span>
            <button
              onClick={startNewConversation}
              className="text-sm px-3 py-1 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700"
            >
              New Chat
            </button>
          </div>
        </div>
      </header>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[60vh] text-center px-4">
              <div className="text-6xl mb-4">📊</div>
              <h2 className="text-2xl font-semibold mb-2">Backtesting Research Agent</h2>
              <p className="text-gray-400 max-w-md mb-6">
                I can help you design trading strategies, run backtests, and analyze results.
                Start by telling me what you'd like to test.
              </p>
              <div className="grid gap-2 text-sm">
                <button
                  onClick={() => sendMessage("What strategies are available?")}
                  className="px-4 py-2 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700 text-left"
                >
                  What strategies are available?
                </button>
                <button
                  onClick={() => sendMessage("Help me design a mean-reversion strategy for ranging markets")}
                  className="px-4 py-2 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700 text-left"
                >
                  Help me design a mean-reversion strategy
                </button>
                <button
                  onClick={() => sendMessage("What is the current market regime for BTCUSDT?")}
                  className="px-4 py-2 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700 text-left"
                >
                  What's the current market regime?
                </button>
              </div>
            </div>
          ) : (
            <div className="py-4">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  toolCalls={message.toolCalls}
                  phase={message.phase}
                  timestamp={message.timestamp}
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

              {/* Loading indicator */}
              {isLoading && (
                <div className="flex items-center gap-3 p-4">
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm">
                    AI
                  </div>
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 rounded-full bg-gray-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input area */}
      <div className="max-w-4xl mx-auto w-full">
        <ChatInput
          onSend={sendMessage}
          disabled={isLoading}
          placeholder="Ask about strategies, run backtests, or get market insights..."
        />
      </div>
    </div>
  );
}
