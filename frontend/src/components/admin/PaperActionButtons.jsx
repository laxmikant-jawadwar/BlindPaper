import { CircleCheck, Download, Eye } from "lucide-react";

/**
 * The row actions of a paper: View (always), Review (only while the paper waits for a decision)
 * and, when `onDownload` is given, a PDF download.
 */
export default function PaperActionButtons({ paper, onView, onReview, onDownload, downloading = false }) {
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => onView(paper)}
        aria-label={`View ${paper.course_name}`}
        className="inline-flex h-8 items-center gap-2 rounded-md bg-[#eef2f8] px-4 text-sm text-slate-600 transition-colors hover:bg-slate-200"
      >
        <Eye className="size-4" aria-hidden="true" />
        View
      </button>
      {paper.status === "Pending Approval" && (
        <button
          type="button"
          onClick={() => onReview(paper)}
          aria-label={`Review ${paper.course_name}`}
          className="inline-flex h-8 items-center gap-2 rounded-md bg-green-600 px-5 text-sm font-medium text-white transition-colors hover:bg-green-700"
        >
          <CircleCheck className="size-4" aria-hidden="true" />
          Review
        </button>
      )}
      {onDownload && (
        <button
          type="button"
          onClick={() => onDownload(paper)}
          disabled={downloading}
          aria-label={`Download PDF of ${paper.course_name}`}
          title="Download PDF"
          className="grid size-8 place-items-center rounded-md border border-slate-200 text-slate-500 transition-colors hover:bg-slate-50 hover:text-brand"
        >
          <Download className="size-4" aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
