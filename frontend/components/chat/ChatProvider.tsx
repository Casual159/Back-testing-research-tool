'use client';

import { createContext, useContext, useState, useCallback, ReactNode, useRef } from 'react';

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

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCall[];
  activeTools?: ActiveTool[];
  phase?: string;
  timestamp: Date;
  isStreaming?: boolean;
}

// Streaming event types from backend
interface StreamEvent {
  type: 'conversation_id' | 'text_delta' | 'tool_start' | 'tool_result' | 'tool_progress' | 'done' | 'error';
  id?: string;
  delta?: string;
  tool?: string;
  args?: Record<string, unknown>;
  result?: Record<string, unknown>;
  success?: boolean;
  conversation_id?: string;
  phase?: string;
  awaiting_confirmation?: boolean;
  confirmation_prompt?: string | null;
  tokens_used?: number;
  cost_usd?: number;
  message?: string;
  data?: Record<string, unknown>;
  // Progress fields
  current?: number;
  total?: number;
  pct?: number;
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
  activeTools: ActiveTool[];
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
  const [activeTools, setActiveTools] = useState<ActiveTool[]>([]);

  // Ref to track the current assistant message ID during streaming
  const streamingMessageIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(async (content: string) => {
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
    setActiveTools([]);

    // Create placeholder assistant message for streaming
    const assistantId = Date.now().toString() + '-assistant';
    streamingMessageIdRef.current = assistantId;

    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      activeTools: [],
      timestamp: new Date(),
      isStreaming: true,
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const response = await fetch('http://localhost:8000/api/agent/chat/stream', {
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

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      const currentActiveTools: ActiveTool[] = [];
      const completedToolCalls: ToolCall[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: StreamEvent = JSON.parse(line.slice(6));

              switch (event.type) {
                case 'conversation_id':
                  if (event.id) {
                    setConversationId(event.id);
                  }
                  break;

                case 'text_delta':
                  if (event.delta) {
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === assistantId
                          ? { ...m, content: m.content + event.delta }
                          : m
                      )
                    );
                  }
                  break;

                case 'tool_start':
                  if (event.tool) {
                    const newTool: ActiveTool = {
                      name: event.tool,
                      args: event.args || {},
                      status: 'running',
                    };
                    currentActiveTools.push(newTool);
                    setActiveTools([...currentActiveTools]);

                    // Update message with active tools
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === assistantId
                          ? { ...m, activeTools: [...currentActiveTools] }
                          : m
                      )
                    );
                  }
                  break;

                case 'tool_result':
                  if (event.tool) {
                    // Update the tool status
                    const toolIndex = currentActiveTools.findIndex(
                      (t) => t.name === event.tool && t.status === 'running'
                    );
                    if (toolIndex !== -1) {
                      currentActiveTools[toolIndex] = {
                        ...currentActiveTools[toolIndex],
                        status: event.success ? 'completed' : 'error',
                        result: event.result,
                        progress: undefined, // Clear progress when done
                      };
                      setActiveTools([...currentActiveTools]);

                      // Add to completed tool calls
                      completedToolCalls.push({
                        tool_name: event.tool,
                        arguments: currentActiveTools[toolIndex].args,
                        timestamp: new Date().toISOString(),
                        result: event.result,
                        success: event.success,
                      });

                      // Update message
                      setMessages((prev) =>
                        prev.map((m) =>
                          m.id === assistantId
                            ? {
                                ...m,
                                activeTools: [...currentActiveTools],
                                toolCalls: [...completedToolCalls],
                              }
                            : m
                        )
                      );
                    }
                  }
                  break;

                case 'tool_progress':
                  if (event.tool) {
                    // Update the tool with progress info
                    const progressToolIndex = currentActiveTools.findIndex(
                      (t) => t.name === event.tool && t.status === 'running'
                    );
                    if (progressToolIndex !== -1) {
                      currentActiveTools[progressToolIndex] = {
                        ...currentActiveTools[progressToolIndex],
                        progress: {
                          current: event.current || 0,
                          total: event.total || 1,
                          pct: event.pct || 0,
                        },
                      };
                      setActiveTools([...currentActiveTools]);

                      // Update message
                      setMessages((prev) =>
                        prev.map((m) =>
                          m.id === assistantId
                            ? { ...m, activeTools: [...currentActiveTools] }
                            : m
                        )
                      );
                    }
                  }
                  break;

                case 'done':
                  if (event.phase) {
                    setCurrentPhase(event.phase);
                  }
                  if (event.tokens_used) {
                    setTotalTokens((prev) => prev + event.tokens_used!);
                  }
                  if (event.cost_usd) {
                    setTotalCost((prev) => prev + event.cost_usd!);
                  }
                  if (event.awaiting_confirmation && event.confirmation_prompt) {
                    setAwaitingConfirmation(true);
                    setConfirmationPrompt(event.confirmation_prompt);
                  }

                  // Finalize message
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? {
                            ...m,
                            isStreaming: false,
                            phase: event.phase,
                            toolCalls: completedToolCalls,
                          }
                        : m
                    )
                  );
                  break;

                case 'error':
                  throw new Error(event.message || 'Unknown streaming error');
              }
            } catch (parseError) {
              console.error('Failed to parse SSE event:', line, parseError);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);

      // Update the streaming message with error
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content:
                  m.content ||
                  `Error: ${error instanceof Error ? error.message : 'Failed to send message'}. Make sure the API server is running.`,
                isStreaming: false,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      setActiveTools([]);
      streamingMessageIdRef.current = null;
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
    setActiveTools([]);
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
        activeTools,
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
