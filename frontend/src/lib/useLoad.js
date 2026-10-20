import { useCallback, useEffect, useEffectEvent, useState } from "react";

/**
 * Load data when a page opens, again when `key` changes (for example the id in the URL), and
 * whenever reload() is called. Returns { data, error, loading, reload }. While reloading, the
 * previous data stays available so the page does not flash empty.
 *
 *   const { data, loading, error, reload } = useLoad(() => api.papers.get(paperId), paperId);
 */
export function useLoad(loader, key = "") {
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState({ id: null, data: null, error: null });

  // the request this render is waiting for; `loading` is true until a result for it arrives
  const id = `${Array.isArray(key) ? JSON.stringify(key) : key}#${version}`;
  const load = useEffectEvent(loader); // always the latest loader, without being a dependency

  useEffect(() => {
    let cancelled = false;
    load()
      .then((data) => !cancelled && setResult({ id, data, error: null }))
      .catch((error) => !cancelled && setResult((previous) => ({ id, data: previous.data, error })));
    return () => {
      cancelled = true;
    };
  }, [id]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { data: result.data, error: result.id === id ? result.error : null, loading: result.id !== id, reload };
}
