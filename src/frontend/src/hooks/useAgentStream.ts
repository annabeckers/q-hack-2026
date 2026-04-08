import { useState, useEffect, useRef, useCallback } from "react";

export interface AgentMessage {
  agent: string;
  content: string;
  type: "thinking" | "response" | "tool_call" | "done";
  timestamp: number;
}

interface UseAgentStreamReturn {
  messages: AgentMessage[];
  isConnected: boolean;
  send: (payload: Record<string, unknown>) => void;
  disconnect: () => void;
}

const WS_URL = "ws://localhost:8000/api/v1/agents/stream";

export function useAgentStream(): UseAgentStreamReturn {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as Omit<AgentMessage, "timestamp">;
        setMessages((prev) => [...prev, { ...data, timestamp: Date.now() }]);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
    };

    ws.onerror = () => ws.close();
  }, []);

  const send = useCallback((payload: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    } else {
      connect();
      // retry after connection
      const interval = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify(payload));
          clearInterval(interval);
        }
      }, 100);
      setTimeout(() => clearInterval(interval), 3000);
    }
  }, [connect]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect]);

  return { messages, isConnected, send, disconnect };
}
