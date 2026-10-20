import { FilePlus2, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, saveBlob } from "../../api/client";
import PaperQuickView from "../../components/papers/PaperQuickView";
import PapersTable from "../../components/papers/PapersTable";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import { buttonClasses } from "../../components/ui/buttonStyles";
import EmptyState from "../../components/ui/EmptyState";
import Modal from "../../components/ui/Modal";
import PageHeading from "../../components/ui/PageHeading";
import Spinner from "../../components/ui/Spinner";
import { STATUS } from "../../lib/constants";
import { useLoad } from "../../lib/useLoad";

const TABS = ["All", STATUS.DRAFT, STATUS.PENDING, STATUS.APPROVED, STATUS.REJECTED];

export default function MyPapers() {
  const { data: papers, loading, error, reload } = useLoad(() => api.papers.list());
  const [tab, setTab] = useState("All");
  const [search, setSearch] = useState("");
  const [quickView, setQuickView] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [notice, setNotice] = useState(null);

  const all = useMemo(() => papers || [], [papers]);
  const counts = useMemo(
    () => Object.fromEntries(TABS.map((t) => [t, t === "All" ? all.length : all.filter((p) => p.status === t).length])),
    [all],
  );
  const shown = useMemo(() => {
    const term = search.trim().toLowerCase();
    return all.filter(
      (p) => (tab === "All" || p.status === tab) && (!term || `${p.course_name} ${p.course_code}`.toLowerCase().includes(term)),
    );
  }, [all, tab, search]);

  const download = async (paper) => {
    setNotice(null);
    try {
      saveBlob(await api.papers.pdf(paper.id));
    } catch (err) {
      setNotice({ tone: "error", text: err.message });
    }
  };

  const confirmDelete = async () => {
    setDeleting(true);
    try {
      await api.papers.remove(toDelete.id);
      setNotice({ tone: "success", text: `"${toDelete.course_name}" was deleted.` });
      setToDelete(null);
      reload();
    } catch (err) {
      setNotice({ tone: "error", text: err.message });
      setToDelete(null);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <PageHeading
        title="My Papers"
        subtitle="Every question paper you have generated, and where it stands."
        actions={
          <Link to="/faculty/generate" className={buttonClasses({ variant: "primary", size: "lg" })}>
            <Plus className="size-5" aria-hidden="true" />
            Generate New Paper
          </Link>
        }
      />

      <section className="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div role="tablist" aria-label="Filter by status" className="flex flex-wrap gap-2">
            {TABS.map((t) => (
              <button
                key={t}
                type="button"
                role="tab"
                aria-selected={tab === t}
                onClick={() => setTab(t)}
                className={`rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                  tab === t ? "bg-brand text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {t} <span className={tab === t ? "text-blue-100" : "text-slate-400"}>({counts[t]})</span>
              </button>
            ))}
          </div>
          <label className="relative block w-full sm:w-72">
            <span className="sr-only">Search papers</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by subject or code"
              className="h-10 w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 text-sm focus:border-brand focus:outline-2 focus:outline-brand/25"
            />
          </label>
        </div>

        {notice && <Alert tone={notice.tone} className="mb-4">{notice.text}</Alert>}
        {error && (
          <Alert tone="error" title="Could not load your papers">
            {error.message}{" "}
            <Button variant="ghost" size="sm" onClick={reload}>
              Try again
            </Button>
          </Alert>
        )}
        {loading && !papers && <Spinner label="Loading your papers..." />}
        {papers && shown.length === 0 && (
          <EmptyState icon={FilePlus2} title={all.length === 0 ? "You have not generated any papers yet" : "No papers match this filter"}>
            {all.length === 0 ? "Upload a syllabus and configure your first question paper." : "Try another status or search term."}
          </EmptyState>
        )}
        {shown.length > 0 && <PapersTable papers={shown} showMarks onQuickView={setQuickView} onDownload={download} onDelete={setToDelete} />}
      </section>

      {quickView && <PaperQuickView paperId={quickView} onClose={() => setQuickView(null)} />}

      <Modal
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        size="md"
        title="Delete this paper?"
        footer={
          <>
            <Button variant="secondary" onClick={() => setToDelete(null)}>
              Keep it
            </Button>
            <Button variant="danger" loading={deleting} onClick={confirmDelete}>
              Delete paper
            </Button>
          </>
        }
      >
        <p className="text-slate-600">
          <strong className="text-ink">{toDelete?.course_name}</strong> ({toDelete?.status}) will be deleted for good. This cannot be undone.
        </p>
      </Modal>
    </>
  );
}
