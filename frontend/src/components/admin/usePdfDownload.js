import { useCallback, useState } from "react";
import { api, saveBlob } from "../../api/client";

/** Download a submitted paper as a PDF. `busyId` is the paper being fetched; `error` is a message to show. */
export function usePdfDownload() {
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState(null);

  const download = useCallback(async (paper) => {
    setError(null);
    setBusyId(paper.id);
    try {
      saveBlob(await api.admin.pdf(paper.id));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);
  return { download, busyId, error, clearError };
}
