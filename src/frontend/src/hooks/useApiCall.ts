import { useEffect, useState, useCallback, useRef } from 'react';

/**
 * Generic hook that calls a typed API function and falls back to mock data on error.
 *
 * Usage:
 *   const { data, loading, error, refetch } = useApiCall(
 *     () => apiClient.getDashboardSummary(),
 *     mockDashboardSummary
 *   );
 */
export function useApiCall<T>(
  apiFn: () => Promise<T>,
  mockFallback: T,
  deps: unknown[] = []
): {
  data: T;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
} {
  const [data, setData] = useState<T>(mockFallback);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFn();
      if (mountedRef.current) {
        setData(result);
      }
    } catch (err) {
      if (mountedRef.current) {
        console.warn('[useApiCall] API failed, using mock fallback:', err);
        setError(err instanceof Error ? err : new Error(String(err)));
        setData(mockFallback);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mountedRef.current = true;
    fetchData();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
