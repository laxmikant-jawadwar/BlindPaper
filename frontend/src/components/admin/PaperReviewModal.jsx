import { CircleCheck, Download, XCircle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import AnalysisPanel from "../paper/AnalysisPanel";
import PaperDocument from "../paper/PaperDocument";
import Alert from "../ui/Alert";
import Button from "../ui/Button";
import Modal from "../ui/Modal";
import Spinner from "../ui/Spinner";
import PaperDetails from "./PaperDetails";
import { useLoad } from "../../lib/useLoad";
import { usePdfDownload } from "./usePdfDownload";

const MIN_REASON = 3;

function analysisBadge(analysis) {
  const fails = analysis.checks.filter((c) => c.status === "fail").length;
  const warns = analysis.checks.filter((c) => c.status === "warn").length;
  if (fails) return { text: `${fails} to fix`, className: "bg-red-100 text-red-700" };
  if (warns) return { text: `${warns} warning${warns > 1 ? "s" : ""}`, className: "bg-amber-100 text-amber-700" };
  return { text: "All passed", className: "bg-green-100 text-green-700" };
}

/**
 * Workflow steps 10 and 11: read the paper, check its marks distribution, syllabus relevance, structure
 * and formatting, then approve it or reject it with a reason the faculty member can act on.
 * `onChanged` fires whenever the paper's status may have changed, so lists behind the modal can refresh.
 */
export default function PaperReviewModal({ paperId, onClose, onDecided, onChanged }) {
  const { data: paper, error, loading, reload } = useLoad(() => api.admin.paper(paperId), [paperId]);
  const pdf = usePdfDownload();
  const [tab, setTab] = useState("paper");
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [reasonError, setReasonError] = useState(null);
  const [busy, setBusy] = useState(null); // "approve" | "reject" | null
  const [actionError, setActionError] = useState(null);
  const reasonField = useRef(null);

  useEffect(() => {
    if (rejecting) reasonField.current?.focus();
  }, [rejecting]);

  const decide = async (decision) => {
    setActionError(null);
    setBusy(decision);
    try {
      const updated = decision === "approve" ? await api.admin.approve(paperId) : await api.admin.reject(paperId, reason.trim());
      onDecided(decision === "approve" ? "approved" : "rejected", updated);
      onClose();
    } catch (err) {
      // e.g. 409: someone else already decided this paper. Show why, and refresh what we are looking at.
      setActionError(err.message);
      setRejecting(false);
      setBusy(null);
      onChanged?.();
      reload();
    }
  };

  const confirmReject = () => {
    if (reason.trim().length < MIN_REASON) {
      setReasonError("Write a reason of at least 3 characters so the faculty member knows what to correct.");
      reasonField.current?.focus();
      return;
    }
    setReasonError(null);
    decide("reject");
  };

  const pending = paper?.status === "Pending Approval";
  const badge = paper && analysisBadge(paper.analysis);

  let footer;
  if (!paper) {
    footer = <Button variant="secondary" onClick={onClose}>Close</Button>;
  } else if (rejecting) {
    footer = (
      <div className="w-full">
        <label htmlFor="rejection-reason" className="mb-1.5 block text-sm font-semibold text-ink">
          Reason for rejection <span className="text-red-600">*</span>
        </label>
        <textarea
          id="rejection-reason"
          ref={reasonField}
          rows={3}
          maxLength={1000}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          aria-invalid={Boolean(reasonError)}
          aria-describedby={reasonError ? "rejection-reason-error" : undefined}
          placeholder="Tell the faculty member what needs to be corrected."
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand focus:outline-2 focus:outline-brand/25"
        />
        {reasonError && (
          <p id="rejection-reason-error" className="mt-1 text-sm text-red-600">
            {reasonError}
          </p>
        )}
        <div className="mt-3 flex justify-end gap-3">
          <Button variant="secondary" disabled={busy === "reject"} onClick={() => { setRejecting(false); setReasonError(null); }}>
            Back
          </Button>
          <Button variant="danger" loading={busy === "reject"} onClick={confirmReject}>
            <XCircle className="size-4" aria-hidden="true" /> Reject paper
          </Button>
        </div>
      </div>
    );
  } else {
    footer = (
      <>
        <Button variant="outline" loading={pdf.busyId === paper.id} onClick={() => pdf.download(paper)} className="mr-auto">
          <Download className="size-4" aria-hidden="true" /> Download PDF
        </Button>
        {pending ? (
          <>
            <Button variant="secondary" onClick={onClose} disabled={busy !== null}>
              Close
            </Button>
            <Button variant="danger" onClick={() => setRejecting(true)} disabled={busy !== null}>
              <XCircle className="size-4" aria-hidden="true" /> Reject
            </Button>
            <Button variant="success" loading={busy === "approve"} disabled={busy !== null} onClick={() => decide("approve")}>
              <CircleCheck className="size-4" aria-hidden="true" /> Approve
            </Button>
          </>
        ) : (
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        )}
      </>
    );
  }

  return (
    <Modal
      open
      onClose={onClose}
      size="xl"
      title={paper ? `Review: ${paper.course_name}` : "Review question paper"}
      subtitle={paper ? `${paper.course_code} · ${paper.faculty_name} · ${paper.department}` : undefined}
      footer={footer}
    >
      {loading && !paper && <Spinner label="Loading the paper..." />}
      {error && <Alert tone="error">{error.message}</Alert>}
      {actionError && (
        <Alert tone="error" title="The decision was not saved" className="mb-4">
          {actionError}
        </Alert>
      )}
      {pdf.error && (
        <Alert tone="error" className="mb-4">
          Could not download the PDF: {pdf.error}
        </Alert>
      )}

      {paper && (
        <div className="space-y-5">
          <PaperDetails paper={paper} />
          {!pending && (
            <Alert tone="info">This paper is {paper.status}, so it can no longer be approved or rejected.</Alert>
          )}

          <div role="tablist" aria-label="Review sections" className="flex gap-1 border-b border-slate-200">
            {[
              { id: "paper", label: "Question paper" },
              { id: "analysis", label: "Review analysis", badge },
            ].map((item) => (
              <button
                key={item.id}
                id={`review-tab-${item.id}`}
                role="tab"
                type="button"
                aria-selected={tab === item.id}
                aria-controls={`review-panel-${item.id}`}
                onClick={() => setTab(item.id)}
                className={`-mb-px flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold transition-colors ${
                  tab === item.id ? "border-brand text-brand" : "border-transparent text-slate-500 hover:text-ink"
                }`}
              >
                {item.label}
                {item.badge && <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${item.badge.className}`}>{item.badge.text}</span>}
              </button>
            ))}
          </div>

          <div role="tabpanel" id={`review-panel-${tab}`} aria-labelledby={`review-tab-${tab}`}>
            {tab === "paper" ? <PaperDocument paper={paper} showAnswers /> : <AnalysisPanel analysis={paper.analysis} />}
          </div>
        </div>
      )}
    </Modal>
  );
}
