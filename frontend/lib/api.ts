// API client functions for the Backtesting Research Tool

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
  message: string;
  session_id?: string | null;
}

export interface ChatResponse {
  message: string;
  session_id?: string | null;
  timestamp: string;
  success: boolean;
}

export interface ChatHealthResponse {
  status: string;
  langflow_url?: string;
  flow_id?: string;
  message?: string;
}

/**
 * Send a message to the chat agent
 */
export async function sendChatMessage(
  message: string,
  sessionId?: string | null
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/agent/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      conversation_id: sessionId,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Check if Langflow is healthy and accessible
 */
export async function checkChatHealth(): Promise<ChatHealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}
