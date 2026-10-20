import { CheckCircle2, XCircle } from "lucide-react";
import { EXAM_TYPES } from "../../lib/constants";
import { formatDate, formatDateTime, formatMarks } from "../../lib/format";
import Alert from "../ui/Alert";
import StatusBadge from "../ui/StatusBadge";

function Item({ label, children }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-0.5 break-words text-sm font-medium text-ink">{children}</dd>
    </div>
  );
}

/** Workflow step 9: subject, course code, faculty, department, exam type, submission date and status. */
export default function PaperDetails({ paper }) {
  const decisions = paper.review_history || [];
  return (
    <div className="space-y-4">
      <dl className="grid gap-x-6 gap-y-4 rounded-xl border border-slate-200 bg-slate-50/60 p-4 sm:grid-cols-2 lg:grid-cols-4">
        <Item label="Subject">{paper.course_name}</Item>
        <Item label="Course code">{paper.course_code}</Item>
        <Item label="Faculty">{paper.faculty_name}</Item>
        <Item label="Department">{paper.department}</Item>
        <Item label="Exam type">{EXAM_TYPES[paper.exam_type].description}</Item>
        <Item label="Year / semester">
          {paper.year}, {paper.semester}
        </Item>
        <Item label="Submitted on">{formatDate(paper.submitted_at)}</Item>
        <Item label="Status">
          <StatusBadge status={paper.status} size="sm" />
        </Item>
        <Item label="Total marks">{formatMarks(paper.total_marks)}</Item>
        <Item label="Difficulty">{paper.difficulty}</Item>
        {paper.reviewed_at && <Item label="Decision on">{formatDateTime(paper.reviewed_at)}</Item>}
      </dl>

      {paper.status === "Rejected" && paper.rejection_reason && (
        <Alert tone="error" title="Rejection reason">
          {paper.rejection_reason}
        </Alert>
      )}

      {decisions.length > 0 && paper.status !== "Rejected" && (
        <section aria-label="Earlier decisions">
          <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-slate-500">Earlier decisions</h3>
          <ul className="space-y-2">
            {decisions.map((decision) => (
              <li key={decision.at} className="flex gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                {decision.status === "Approved" ? (
                  <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-green-600" aria-hidden="true" />
                ) : (
                  <XCircle className="mt-0.5 size-5 shrink-0 text-red-500" aria-hidden="true" />
                )}
                <span>
                  <span className="font-semibold">{decision.status}</span> by {decision.by} on {formatDateTime(decision.at)}
                  {decision.reason && <span className="block text-slate-600">{decision.reason}</span>}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
