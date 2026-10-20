import { FileText } from "lucide-react";
import { formatDate } from "../../lib/format";
import EmptyState from "../ui/EmptyState";
import StatusBadge from "../ui/StatusBadge";
import { bodyRow, headRow, table, th } from "./tableStyles";

const cell = "px-2 py-2 text-[12.5px]";

/** The latest submissions of any status. A subject opens the paper. */
export default function RecentSubmissionsTable({ papers, onView }) {
  if (papers.length === 0) {
    return (
      <EmptyState icon={FileText} title="Nothing has been submitted yet">
        The latest papers submitted by faculty will appear here.
      </EmptyState>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className={`${table} min-w-[520px]`}>
        <thead>
          <tr className={headRow}>
            <th className={`${th} w-8 px-2`}>#</th>
            <th className={`${th} px-2`}>Subject</th>
            <th className={`${th} px-2`}>Department</th>
            <th className={`${th} px-2`}>Faculty</th>
            <th className={`${th} px-2`}>Submitted On</th>
            <th className={`${th} px-2`}>Status</th>
          </tr>
        </thead>
        <tbody>
          {papers.map((paper, index) => (
            <tr key={paper.id} className={bodyRow}>
              <td className={`${cell} text-ink`}>{index + 1}</td>
              <td className={cell}>
                <button
                  type="button"
                  onClick={() => onView(paper)}
                  className="text-left font-medium text-ink hover:text-brand hover:underline"
                >
                  {paper.course_name}
                </button>
              </td>
              <td className={`${cell} text-slate-500`}>{paper.department}</td>
              <td className={`${cell} whitespace-nowrap text-slate-500`}>{paper.faculty_name}</td>
              <td className={`${cell} whitespace-nowrap text-slate-500`}>{formatDate(paper.submitted_at)}</td>
              <td className={cell}>
                <StatusBadge status={paper.status} label={paper.status === "Pending Approval" ? "Pending" : undefined} size="sm" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
