import { useEffect, useRef, useState, useCallback } from 'react';

interface UseApiOptions {
  delay?: number;
  mockFallback?: unknown;
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useApi<T>(
  url: string,
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const { delay = 800, mockFallback = null } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(url, {
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        // Fallback to mock data with simulated delay
        const mockDataWithDelay = new Promise<void>((resolve) => {
          setTimeout(() => {
            setData(mockFallback as T);
            setError(null);
            resolve();
          }, delay);
        });

        await mockDataWithDelay;
      }
    } finally {
      setLoading(false);
    }
  }, [url, delay, mockFallback]);

  useEffect(() => {
    fetchData();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchData]);

  const refetch = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
}
