import { FileText, Search } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import PaperActionButtons from "../../components/admin/PaperActionButtons";
import PaperReviewModal from "../../components/admin/PaperReviewModal";
import PaperViewModal from "../../components/admin/PaperViewModal";
import { bodyRow, headRow, table, td, tdMuted, th } from "../../components/admin/tableStyles";
import { useLoad } from "../../lib/useLoad";
import { usePdfDownload } from "../../components/admin/usePdfDownload";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import EmptyState from "../../components/ui/EmptyState";
import { inputClasses } from "../../components/ui/FormField";
import PageHeading from "../../components/ui/PageHeading";
import Spinner from "../../components/ui/Spinner";
import StatusBadge from "../../components/ui/StatusBadge";
import { DEPARTMENTS, EXAM_TYPES, STATUS } from "../../lib/constants";
import { formatDate } from "../../lib/format";

const TABS = [
  { value: "", label: "All" },
  { value: STATUS.PENDING, label: "Pending Approval" },
  { value: STATUS.APPROVED, label: "Approved" },
  { value: STATUS.REJECTED, label: "Rejected" },
];

export default function AdminAllPapers() {
  // The filters live in the URL, so "View All" links from the dashboard open already filtered
  const [params, setParams] = useSearchParams();
  const status = params.get("status") || "";
  const department = params.get("department") || "";
  const q = params.get("q") || "";

  const [search, setSearch] = useState(q);
  const [viewId, setViewId] = useState(null);
  const [reviewId, setReviewId] = useState(null);
  const [notice, setNotice] = useState(null);
  const pdf = usePdfDownload();

  const papers = useLoad(() => api.admin.papers({ status, department, q }), [status, department, q]);

  const setFilter = useCallback(
    (changes) =>
      setParams(
        (current) => {
          const next = new URLSearchParams(current);
          Object.entries(changes).forEach(([key, value]) => (value ? next.set(key, value) : next.delete(key)));
          return next;
        },
        { replace: true },
      ),
    [setParams],
  );

  // wait for a pause in typing before searching
  useEffect(() => {
    if (search.trim() === q) return;
    const timer = setTimeout(() => setFilter({ q: search.trim() }), 300);
    return () => clearTimeout(timer);
  }, [search, q, setFilter]);

  const clearFilters = () => {
    setSearch("");
    setParams({}, { replace: true });
  };

  const rows = papers.data || [];
  const filtered = Boolean(status || department || q);

  return (
    <div className="mx-auto max-w-[1400px]">
      <PageHeading title="All Papers" subtitle="Every paper submitted by faculty, newest first." />

      {notice && (
        <Alert tone="success" className="mb-5">
          <span className="flex items-center justify-between gap-4">
            {notice}
            <button type="button" onClick={() => setNotice(null)} className="font-semibold underline">
              Dismiss
            </button>
          </span>
        </Alert>
      )}
      {papers.error && (
        <Alert tone="error" title="The papers could not be loaded" className="mb-5">
          <p>{papers.error.message}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={papers.reload}>
            Try again
          </Button>
        </Alert>
      )}
      {pdf.error && (
        <Alert tone="error" className="mb-5">
          Could not download the PDF: {pdf.error}
        </Alert>
      )}

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3">
        <div role="tablist" aria-label="Filter by status" className="flex flex-wrap gap-2">
          {TABS.map((tab) => (
            <button
              key={tab.label}
              role="tab"
              type="button"
              aria-selected={status === tab.value}
              onClick={() => setFilter({ status: tab.value })}
              className={`h-10 rounded-md px-4 text-[15px] transition-colors ${
                status === tab.value ? "bg-brand font-medium text-white shadow-sm" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex w-full flex-wrap items-center gap-3 lg:w-auto">
          <div className="w-full sm:w-56">
            <label className="sr-only" htmlFor="papers-department">
              Department
            </label>
            <select
              id="papers-department"
              value={department}
              onChange={(event) => setFilter({ department: event.target.value })}
              className={inputClasses}
            >
              <option value="">All Departments</option>
              {DEPARTMENTS.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div className="relative w-full sm:w-80">
            <label className="sr-only" htmlFor="papers-search">
              Search papers
            </label>
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
            <input
              id="papers-search"
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search subject, code or faculty"
              className={`${inputClasses} pl-9`}
            />
          </div>
        </div>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-3 sm:p-4" aria-live="polite">
        {papers.loading && !papers.data ? (
          <div className="py-12 text-center">
            <Spinner label="Loading papers..." />
          </div>
        ) : rows.length === 0 ? (
          <EmptyState icon={FileText} title={filtered ? "No papers match these filters" : "No papers have been submitted yet"}>
            {filtered ? (
              <Button variant="secondary" size="sm" className="mt-3" onClick={clearFilters}>
                Clear filters
              </Button>
            ) : (
              "Papers appear here once faculty submit them for approval."
            )}
          </EmptyState>
        ) : (
          <div className={`overflow-x-auto rounded-lg border border-slate-200 ${papers.loading ? "opacity-60" : ""}`}>
            <table className={`${table} min-w-[1000px]`}>
              <thead>
                <tr className={headRow}>
                  <th className={`${th} w-12`}>#</th>
                  <th className={th}>Subject</th>
                  <th className={th}>Department</th>
                  <th className={th}>Faculty</th>
                  <th className={th}>Exam Type</th>
                  <th className={th}>Submitted On</th>
                  <th className={th}>Status</th>
                  <th className={th}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((paper, index) => (
                  <tr key={paper.id} className={bodyRow}>
                    <td className={td}>{index + 1}</td>
                    <td className={td}>
                      <span className="font-medium">{paper.course_name}</span>
                      <span className="block text-xs text-slate-500">{paper.course_code}</span>
                    </td>
                    <td className={tdMuted}>{paper.department}</td>
                    <td className={`${tdMuted} whitespace-nowrap`}>{paper.faculty_name}</td>
                    <td className={`${tdMuted} whitespace-nowrap`}>{EXAM_TYPES[paper.exam_type].short}</td>
                    <td className={`${tdMuted} whitespace-nowrap`}>{formatDate(paper.submitted_at)}</td>
                    <td className={td}>
                      <StatusBadge status={paper.status} size="sm" />
                    </td>
                    <td className="px-3 py-2">
                      <PaperActionButtons
                        paper={paper}
                        onView={(row) => setViewId(row.id)}
                        onReview={(row) => setReviewId(row.id)}
                        onDownload={pdf.download}
                        downloading={pdf.busyId === paper.id}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {rows.length > 0 && (
          <p className="mt-3 text-sm text-slate-500">
            Showing {rows.length} paper{rows.length === 1 ? "" : "s"}.
          </p>
        )}
      </section>

      {viewId && <PaperViewModal paperId={viewId} onClose={() => setViewId(null)} />}
      {reviewId && (
        <PaperReviewModal
          paperId={reviewId}
          onClose={() => setReviewId(null)}
          onDecided={(decision, paper) => {
            setNotice(`"${paper.course_name}" by ${paper.faculty_name} was ${decision}.`);
            papers.reload();
          }}
          onChanged={papers.reload}
        />
      )}
    </div>
  );
}
