'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

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

interface ChatContextType {
  messages: Message[];
  conversationId: string | null;
  isLoading: boolean;
  isOpen: boolean;
  awaitingConfirmation: boolean;
  confirmationPrompt: string | null;
  currentPhase: string;
  totalCost: number;
  totalTokens: number;
  sendMessage: (content: string) => Promise<void>;
  handleConfirm: () => void;
  handleCancel: () => void;
  startNewConversation: () => void;
  toggleSidebar: () => void;
  openSidebar: () => void;
  closeSidebar: () => void;
}

const ChatContext = createContext<ChatContextType | null>(null);

export function useChatContext() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within ChatProvider');
  }
  return context;
}

interface ChatProviderProps {
  children: ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [confirmationPrompt, setConfirmationPrompt] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState<string>('CONVERSATION');
  const [totalCost, setTotalCost] = useState(0);
  const [totalTokens, setTotalTokens] = useState(0);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

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

      setConversationId(data.conversation_id);
      setCurrentPhase(data.phase);
      setTotalCost((prev) => prev + data.cost_usd);
      setTotalTokens((prev) => prev + data.tokens_used);

      const assistantMessage: Message = {
        id: Date.now().toString() + '-assistant',
        role: 'assistant',
        content: data.message,
        toolCalls: data.tool_calls,
        phase: data.phase,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

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
  }, [conversationId, isLoading]);

  const handleConfirm = useCallback(() => {
    sendMessage('Yes, proceed');
  }, [sendMessage]);

  const handleCancel = useCallback(() => {
    sendMessage("No, let me reconsider");
  }, [sendMessage]);

  const startNewConversation = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setCurrentPhase('CONVERSATION');
    setAwaitingConfirmation(false);
    setConfirmationPrompt(null);
    setTotalCost(0);
    setTotalTokens(0);
  }, []);

  const toggleSidebar = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const openSidebar = useCallback(() => {
    setIsOpen(true);
  }, []);

  const closeSidebar = useCallback(() => {
    setIsOpen(false);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        conversationId,
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
        toggleSidebar,
        openSidebar,
        closeSidebar,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}
