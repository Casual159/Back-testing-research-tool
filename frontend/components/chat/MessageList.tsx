import React, { useEffect, useRef } from "react";
import Message, { MessageProps } from "./Message";

interface MessageListProps {
  messages: MessageProps[];
  isLoading?: boolean;
}

export default function MessageList({ messages, isLoading }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-neutral-500 dark:text-neutral-400 text-sm">
          <div className="text-center">
            <div className="mb-2">Start a conversation with the Research Assistant</div>
            <div className="text-xs">Ask about data, strategies, or market analysis</div>
          </div>
        </div>
      ) : (
        messages.map((msg, index) => (
          <Message
            key={index}
            role={msg.role}
            content={msg.content}
            timestamp={msg.timestamp}
          />
        ))
      )}
      {isLoading && (
        <div className="flex justify-start mb-4">
          <div className="max-w-[80%] rounded-lg px-4 py-2 bg-neutral-200 dark:bg-neutral-700">
            <div className="text-sm font-medium mb-1">Research Assistant</div>
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <div className="w-2 h-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <div className="w-2 h-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}
