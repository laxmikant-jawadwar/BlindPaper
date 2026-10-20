import { Download, Eye, Pencil, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { EXAM_TYPES } from "../../lib/constants";
import { formatDate } from "../../lib/format";
import { buttonClasses } from "../ui/buttonStyles";
import StatusBadge from "../ui/StatusBadge";

const ICON_BUTTON =
  "grid size-10 place-items-center rounded-lg border border-slate-200 bg-white text-slate-700 transition-colors hover:bg-slate-50";

/**
 * The faculty's papers as a table: # Subject Department Exam Type Generated On Status Actions.
 * The eye button is a quick look (onQuickView); View/Edit opens the full page.
 */
export default function PapersTable({ papers, onQuickView, onDownload, onDelete, showMarks = false }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full min-w-[820px] text-left text-[15px]">
        <thead className="bg-slate-50 text-sm font-semibold text-ink">
          <tr>
            <th scope="col" className="w-12 px-4 py-3.5">#</th>
            <th scope="col" className="px-3 py-3.5">Subject</th>
            <th scope="col" className="px-3 py-3.5">Department</th>
            <th scope="col" className="px-3 py-3.5">Exam Type</th>
            <th scope="col" className="px-3 py-3.5">Generated On</th>
            {showMarks && <th scope="col" className="px-3 py-3.5">Marks</th>}
            <th scope="col" className="px-3 py-3.5">Status</th>
            <th scope="col" className="px-4 py-3.5 text-center">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {papers.map((paper, index) => {
            const editable = paper.status === "Draft" || paper.status === "Rejected";
            return (
              <tr key={paper.id} className="bg-white hover:bg-slate-50/60">
                <td className="px-4 py-4 text-ink">{index + 1}</td>
                <td className="px-3 py-4 font-medium text-ink">
                  {paper.course_name}
                  <span className="block text-xs font-normal text-slate-400">{paper.course_code}</span>
                </td>
                <td className="px-3 py-4 text-slate-600">{paper.department || "—"}</td>
                <td className="px-3 py-4 text-slate-600">{EXAM_TYPES[paper.exam_type]?.short}</td>
                <td className="whitespace-nowrap px-3 py-4 text-slate-600">{formatDate(paper.created_at)}</td>
                {showMarks && <td className="px-3 py-4 text-slate-600">{paper.total_marks}</td>}
                <td className="px-3 py-4">
                  <StatusBadge status={paper.status} />
                  {paper.status === "Rejected" && paper.rejection_reason && (
                    <span className="mt-1 block max-w-[220px] truncate text-xs text-red-600" title={paper.rejection_reason}>
                      {paper.rejection_reason}
                    </span>
                  )}
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center justify-center gap-2">
                    <button type="button" onClick={() => onQuickView(paper.id)} aria-label={`Quick view of ${paper.course_name}`} className={ICON_BUTTON}>
                      <Eye className="size-5" aria-hidden="true" />
                    </button>
                    <Link to={`/faculty/papers/${paper.id}`} className={buttonClasses({ variant: "soft", className: "w-[72px]" })}>
                      {editable && <Pencil className="size-4" aria-hidden="true" />}
                      {editable ? "Edit" : "View"}
                    </Link>
                    {onDownload && paper.status === "Approved" && (
                      <button type="button" onClick={() => onDownload(paper)} aria-label={`Download ${paper.course_name} as PDF`} className={ICON_BUTTON}>
                        <Download className="size-5" aria-hidden="true" />
                      </button>
                    )}
                    {onDelete && editable && (
                      <button
                        type="button"
                        onClick={() => onDelete(paper)}
                        aria-label={`Delete ${paper.course_name}`}
                        className={`${ICON_BUTTON} text-red-600 hover:bg-red-50`}
                      >
                        <Trash2 className="size-5" aria-hidden="true" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
