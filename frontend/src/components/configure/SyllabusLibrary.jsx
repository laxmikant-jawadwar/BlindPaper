import { FileText, RefreshCw, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { formatDate } from "../../lib/format";
import Alert from "../ui/Alert";
import Button from "../ui/Button";
import { buttonClasses } from "../ui/buttonStyles";
import EmptyState from "../ui/EmptyState";
import Modal from "../ui/Modal";
import Spinner from "../ui/Spinner";

/** "Your syllabi": everything this faculty member has uploaded, ready to configure a paper from. */
export default function SyllabusLibrary({ refreshKey }) {
  const [state, setState] = useState({ key: null, items: [], error: null });
  const [reload, setReload] = useState(0);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const requestKey = `${refreshKey}-${reload}`;
  useEffect(() => {
    let cancelled = false;
    api.syllabus
      .list()
      .then((items) => !cancelled && setState({ key: requestKey, items, error: null }))
      .catch((error) => !cancelled && setState({ key: requestKey, items: [], error }));
    return () => {
      cancelled = true;
    };
  }, [requestKey]);

  const loading = state.key !== requestKey;

  const confirmDelete = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      await api.syllabus.remove(toDelete.id);
      setState((current) => ({ ...current, items: current.items.filter((item) => item.id !== toDelete.id) }));
      setToDelete(null);
    } catch (err) {
      setDeleteError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
        <div>
          <h2 className="text-lg font-bold text-ink">Your syllabi</h2>
          <p className="text-sm text-slate-500">Pick one you have already uploaded to configure another paper.</p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => setReload((n) => n + 1)} aria-label="Refresh the list">
          <RefreshCw className="size-4" aria-hidden="true" /> Refresh
        </Button>
      </div>

      {loading ? (
        <div className="px-5 py-10 text-center">
          <Spinner label="Loading your syllabi..." />
        </div>
      ) : state.error ? (
        <div className="p-5">
          <Alert tone="error" title="Could not load your syllabi">
            {state.error.message}
          </Alert>
        </div>
      ) : state.items.length === 0 ? (
        <EmptyState icon={FileText} title="No syllabi yet">
          Upload a syllabus PDF above. It will appear here so you can reuse it for later papers.
        </EmptyState>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-5 py-3 font-semibold">Course</th>
                <th className="px-3 py-3 font-semibold">Code</th>
                <th className="px-3 py-3 font-semibold">Units</th>
                <th className="px-3 py-3 font-semibold">Uploaded</th>
                <th className="px-5 py-3 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {state.items.map((item) => (
                <tr key={item.id}>
                  <td className="px-5 py-3.5">
                    <div className="font-medium text-ink">{item.subject_name}</div>
                    <div className="text-xs text-slate-500">{item.filename}</div>
                  </td>
                  <td className="px-3 py-3.5 text-slate-600">{item.course_code || "—"}</td>
                  <td className="px-3 py-3.5 text-slate-600">{item.unit_count}</td>
                  <td className="px-3 py-3.5 text-slate-600">{formatDate(item.created_at)}</td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center justify-end gap-2">
                      {item.unit_count > 0 ? (
                        <Link to={`/faculty/generate/${item.id}`} className={buttonClasses({ variant: "primary", size: "sm" })}>
                          Use this syllabus
                        </Link>
                      ) : (
                        <span className="text-xs text-amber-700" title="No unit headings were found in this PDF">
                          No units found
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          setDeleteError(null);
                          setToDelete(item);
                        }}
                        aria-label={`Delete ${item.subject_name}`}
                        className="grid size-9 place-items-center rounded-lg border border-slate-200 text-slate-500 hover:border-red-200 hover:bg-red-50 hover:text-red-600"
                      >
                        <Trash2 className="size-4" aria-hidden="true" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={Boolean(toDelete)}
        onClose={() => !deleting && setToDelete(null)}
        title="Delete this syllabus?"
        size="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setToDelete(null)} disabled={deleting}>
              Keep it
            </Button>
            <Button variant="danger" onClick={confirmDelete} loading={deleting}>
              Delete syllabus
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-600">
          <strong className="text-ink">{toDelete?.subject_name}</strong> ({toDelete?.filename}) will be removed from your account. Papers you already generated from it are kept.
        </p>
        {deleteError && (
          <Alert tone="error" className="mt-3">
            {deleteError}
          </Alert>
        )}
      </Modal>
    </section>
  );
}
