'use client';

import { createContext, useContext, useState, useCallback, ReactNode, useRef } from 'react';
import { useProject } from '@/lib/contexts';
import { apiEndpoint } from '@/lib/config';

// =============================================================================
// Types - Block-based message structure
// =============================================================================

export interface TextBlock {
  type: 'text';
  content: string;
}

export interface ToolBlock {
  type: 'tool';
  id: string;
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

export type MessageBlock = TextBlock | ToolBlock;

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  blocks: MessageBlock[];
  timestamp: Date;
  isStreaming?: boolean;
  phase?: string;
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
  chatWidth: number;
  setChatWidth: (width: number) => void;
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
  const [chatWidth, setChatWidth] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('chat_sidebar_width');
      return stored ? parseInt(stored, 10) : 420;
    }
    return 420;
  });
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [confirmationPrompt, setConfirmationPrompt] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState<string>('CONVERSATION');
  const [totalCost, setTotalCost] = useState(0);
  const [totalTokens, setTotalTokens] = useState(0);

  // Get current project for timeline events
  const { currentProject, refreshEvents } = useProject();

  // Ref to track the current assistant message ID during streaming
  const streamingMessageIdRef = useRef<string | null>(null);
  // Counter for unique tool IDs
  const toolIdCounterRef = useRef(0);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Add user message with blocks structure
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      blocks: [{ type: 'text', content }],
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setAwaitingConfirmation(false);

    // Create placeholder assistant message for streaming
    const assistantId = Date.now().toString() + '-assistant';
    streamingMessageIdRef.current = assistantId;

    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      blocks: [],
      timestamp: new Date(),
      isStreaming: true,
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const response = await fetch(apiEndpoint('/agent/chat/stream'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          conversation_id: conversationId,
          project_id: currentProject?.id || null,  // Include project for timeline events
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

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

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
                      prev.map((m) => {
                        if (m.id !== assistantId) return m;

                        const blocks = [...m.blocks];
                        const lastBlock = blocks[blocks.length - 1];

                        // If last block is text, append to it
                        if (lastBlock?.type === 'text') {
                          blocks[blocks.length - 1] = {
                            ...lastBlock,
                            content: lastBlock.content + event.delta,
                          };
                        } else {
                          // Otherwise create new text block
                          blocks.push({ type: 'text', content: event.delta! });
                        }

                        return { ...m, blocks };
                      })
                    );
                  }
                  break;

                case 'tool_start':
                  if (event.tool) {
                    const toolId = `tool-${++toolIdCounterRef.current}`;
                    const toolBlock: ToolBlock = {
                      type: 'tool',
                      id: toolId,
                      name: event.tool,
                      args: event.args || {},
                      status: 'running',
                    };

                    setMessages((prev) =>
                      prev.map((m) => {
                        if (m.id !== assistantId) return m;
                        return { ...m, blocks: [...m.blocks, toolBlock] };
                      })
                    );
                  }
                  break;

                case 'tool_result':
                  if (event.tool) {
                    setMessages((prev) =>
                      prev.map((m) => {
                        if (m.id !== assistantId) return m;

                        const blocks = m.blocks.map((block) => {
                          if (
                            block.type === 'tool' &&
                            block.name === event.tool &&
                            block.status === 'running'
                          ) {
                            return {
                              ...block,
                              status: event.success ? 'completed' : 'error',
                              result: event.result,
                              progress: undefined,
                            } as ToolBlock;
                          }
                          return block;
                        });

                        return { ...m, blocks };
                      })
                    );
                  }
                  break;

                case 'tool_progress':
                  if (event.tool) {
                    setMessages((prev) =>
                      prev.map((m) => {
                        if (m.id !== assistantId) return m;

                        const blocks = m.blocks.map((block) => {
                          if (
                            block.type === 'tool' &&
                            block.name === event.tool &&
                            block.status === 'running'
                          ) {
                            return {
                              ...block,
                              progress: {
                                current: event.current || 0,
                                total: event.total || 1,
                                pct: event.pct || 0,
                              },
                            } as ToolBlock;
                          }
                          return block;
                        });

                        return { ...m, blocks };
                      })
                    );
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
                          }
                        : m
                    )
                  );

                  // Refresh timeline events (in case tools created new events)
                  if (currentProject?.id) {
                    refreshEvents();
                  }
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
        prev.map((m) => {
          if (m.id !== assistantId) return m;

          const errorText =
            error instanceof Error ? error.message : 'Failed to send message';
          const hasContent = m.blocks.some(
            (b) => b.type === 'text' && b.content.trim()
          );

          if (hasContent) {
            return { ...m, isStreaming: false };
          }

          return {
            ...m,
            blocks: [
              {
                type: 'text',
                content: `Error: ${errorText}. Make sure the API server is running.`,
              },
            ],
            isStreaming: false,
          };
        })
      );
    } finally {
      setIsLoading(false);
      streamingMessageIdRef.current = null;
    }
  }, [conversationId, isLoading, currentProject?.id, refreshEvents]);

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
    toolIdCounterRef.current = 0;
  }, []);

  const toggleSidebar = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const handleSetChatWidth = useCallback((width: number) => {
    const clamped = Math.min(Math.max(width, 320), 800);
    setChatWidth(clamped);
    localStorage.setItem('chat_sidebar_width', String(clamped));
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
        chatWidth,
        setChatWidth: handleSetChatWidth,
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
