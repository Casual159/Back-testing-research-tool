import React from "react";

export interface MessageProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: Date;
}

export default function Message({ role, content, timestamp }: MessageProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-neutral-200 dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100"
        }`}
      >
        <div className="text-sm font-medium mb-1">
          {isUser ? "You" : "Research Assistant"}
        </div>
        <div className="text-sm whitespace-pre-wrap break-words">
          {content}
        </div>
        {timestamp && (
          <div className="text-xs opacity-70 mt-1">
            {new Date(timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
