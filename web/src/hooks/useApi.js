import { useState, useEffect, useCallback } from 'react';

export function useApi(apiFn, ...args) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await apiFn(...args));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [apiFn, ...args]);
  useEffect(() => {
    fetch();
  }, [fetch]);
  return { data, loading, error, refetch: fetch };
}

export function useLazyApi(apiFn) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const execute = useCallback(
    async (...args) => {
      setLoading(true);
      setError(null);
      try {
        const r = await apiFn(...args);
        setData(r);
        return r;
      } catch (e) {
        setError(e.message);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [apiFn]
  );
  return { data, loading, error, execute };
}
