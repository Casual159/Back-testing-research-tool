"use client";

import React, { useState } from "react";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import { MessageProps } from "./Message";

export default function ChatSidebar() {
  const [messages, setMessages] = useState<MessageProps[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendMessage = async (text: string) => {
    // Add user message immediately
    const userMessage: MessageProps = {
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update session ID if provided
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      // Add assistant response
      const assistantMessage: MessageProps = {
        role: "assistant",
        content: data.message,
        timestamp: new Date(data.timestamp),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);

      // Add error message
      const errorMessage: MessageProps = {
        role: "assistant",
        content: `Error: Could not send message. ${error instanceof Error ? error.message : "Please check if the backend is running."}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-80 h-screen border-r border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-neutral-300 dark:border-neutral-700">
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
          Research Assistant
        </h2>
        <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1">
          Ask about data, strategies, or analysis
        </p>
      </div>

      {/* Messages */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Input */}
      <div className="p-4 border-t border-neutral-300 dark:border-neutral-700">
        <MessageInput onSend={sendMessage} disabled={isLoading} />
      </div>
    </div>
  );
}
