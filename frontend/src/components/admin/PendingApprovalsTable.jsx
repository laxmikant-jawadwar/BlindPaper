import { CircleCheck } from "lucide-react";
import { EXAM_TYPES } from "../../lib/constants";
import { formatDate } from "../../lib/format";
import EmptyState from "../ui/EmptyState";
import PaperActionButtons from "./PaperActionButtons";
import { bodyRow, headRow, table, td, tdMuted, th } from "./tableStyles";

/** The papers waiting for a decision: # | Subject | Department | Faculty | Exam Type | Submitted On | Actions. */
export default function PendingApprovalsTable({ papers, onView, onReview }) {
  if (papers.length === 0) {
    return (
      <EmptyState icon={CircleCheck} title="No papers are waiting for approval">
        New submissions from faculty will appear here.
      </EmptyState>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className={`${table} min-w-[900px]`}>
        <thead>
          <tr className={headRow}>
            <th className={`${th} w-12`}>#</th>
            <th className={th}>Subject</th>
            <th className={th}>Department</th>
            <th className={th}>Faculty</th>
            <th className={th}>Exam Type</th>
            <th className={th}>Submitted On</th>
            <th className={th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {papers.map((paper, index) => (
            <tr key={paper.id} className={bodyRow}>
              <td className={td}>{index + 1}</td>
              <td className={`${td} font-medium`}>{paper.course_name}</td>
              <td className={tdMuted}>{paper.department}</td>
              <td className={tdMuted}>{paper.faculty_name}</td>
              <td className={tdMuted}>{EXAM_TYPES[paper.exam_type].short}</td>
              <td className={tdMuted}>{formatDate(paper.submitted_at)}</td>
              <td className="px-3 py-1.5">
                <PaperActionButtons paper={paper} onView={onView} onReview={onReview} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
