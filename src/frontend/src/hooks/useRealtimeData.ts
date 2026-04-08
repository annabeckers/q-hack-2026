import { useState, useEffect, useRef, useCallback } from "react";

export interface RealtimeDataPoint {
  [key: string]: unknown;
}

interface UseRealtimeDataOptions {
  url?: string;
  bufferSize?: number;
  autoConnect?: boolean;
}

interface UseRealtimeDataReturn<T extends RealtimeDataPoint> {
  points: T[];
  isConnected: boolean;
  clear: () => void;
}

const DEFAULT_URL = "ws://localhost:8000/api/v1/data/stream";
const DEFAULT_BUFFER_SIZE = 100;

export function useRealtimeData<T extends RealtimeDataPoint = RealtimeDataPoint>(
  options: UseRealtimeDataOptions = {},
): UseRealtimeDataReturn<T> {
  const {
    url = DEFAULT_URL,
    bufferSize = DEFAULT_BUFFER_SIZE,
    autoConnect = true,
  } = options;

  const [points, setPoints] = useState<T[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const bufferSizeRef = useRef(bufferSize);

  // Keep buffer size ref in sync
  bufferSizeRef.current = bufferSize;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as T;
        setPoints((prev) => {
          const next = [...prev, data];
          if (next.length > bufferSizeRef.current) {
            return next.slice(next.length - bufferSizeRef.current);
          }
          return next;
        });
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
    };

    ws.onerror = () => ws.close();
  }, [url]);

  const clear = useCallback(() => {
    setPoints([]);
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect, autoConnect]);

  return { points, isConnected, clear };
}
