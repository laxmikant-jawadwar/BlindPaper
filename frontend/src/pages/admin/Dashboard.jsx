import { ChartNoAxesColumn, Check, Clock, FileText, X } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import DepartmentFilter from "../../components/admin/DepartmentFilter";
import DepartmentSummary from "../../components/admin/DepartmentSummary";
import PaperReviewModal from "../../components/admin/PaperReviewModal";
import PaperViewModal from "../../components/admin/PaperViewModal";
import PendingApprovalsTable from "../../components/admin/PendingApprovalsTable";
import RecentSubmissionsTable from "../../components/admin/RecentSubmissionsTable";
import SectionCard from "../../components/admin/SectionCard";
import { useLoad } from "../../lib/useLoad";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import PageHeading from "../../components/ui/PageHeading";
import Spinner from "../../components/ui/Spinner";
import StatCard from "../../components/ui/StatCard";
import { STATUS } from "../../lib/constants";

const ROWS_SHOWN = 5;

export default function AdminDashboard() {
  const [department, setDepartment] = useState(""); // "" means all departments
  const [viewId, setViewId] = useState(null);
  const [reviewId, setReviewId] = useState(null);
  const [notice, setNotice] = useState(null);

  const stats = useLoad(() => api.admin.stats(department || undefined), [department]);
  const papers = useLoad(() => api.admin.papers({ department: department || undefined }), [department]);

  const refresh = () => {
    stats.reload();
    papers.reload();
  };

  const onDecided = (decision, paper) => {
    setNotice({ tone: "success", text: `"${paper.course_name}" by ${paper.faculty_name} was ${decision}.` });
    refresh();
  };

  const all = papers.data || [];
  const pending = all.filter((paper) => paper.status === STATUS.PENDING);
  const recent = all.slice(0, ROWS_SHOWN);
  const counts = stats.data;
  const failed = stats.error || papers.error;
  const value = (key) => (counts ? counts[key] : "–");
  const inDepartment = department ? `&department=${encodeURIComponent(department)}` : "";

  return (
    <div className="mx-auto max-w-[1400px]">
      <PageHeading title="Welcome, Admin" subtitle="Review and approve AI-generated question papers" />

      {notice && (
        <Alert tone={notice.tone} className="mb-5">
          <span className="flex items-center justify-between gap-4">
            {notice.text}
            <button type="button" onClick={() => setNotice(null)} className="font-semibold underline">
              Dismiss
            </button>
          </span>
        </Alert>
      )}

      {failed && (
        <Alert tone="error" title="The dashboard could not be loaded" className="mb-5">
          <p>{failed.message}</p>
          <Button variant="secondary" size="sm" className="mt-2" onClick={refresh}>
            Try again
          </Button>
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard compact tone="blue" icon={FileText} value={value("total")} label="Total Papers" />
        <StatCard compact tone="orange" icon={Clock} value={value("pending")} label="Pending Approval" />
        <StatCard compact tone="green" icon={Check} value={value("approved")} label="Approved" />
        <StatCard compact tone="red" icon={X} value={value("rejected")} label="Rejected" />
      </div>

      <div className="mt-5">
        <DepartmentFilter value={department} onChange={setDepartment} />
      </div>

      <SectionCard
        className="mt-5"
        icon={Clock}
        tone="amber"
        title="Pending Paper Approvals"
        viewAllTo={`/admin/papers?status=${encodeURIComponent(STATUS.PENDING)}${inDepartment}`}
      >
        {papers.loading && !papers.data ? (
          <div className="py-10 text-center">
            <Spinner label="Loading papers..." />
          </div>
        ) : (
          <>
            <PendingApprovalsTable papers={pending.slice(0, ROWS_SHOWN)} onView={(paper) => setViewId(paper.id)} onReview={(paper) => setReviewId(paper.id)} />
            {pending.length > ROWS_SHOWN && (
              <p className="mt-3 text-center text-sm text-slate-500">
                Showing {ROWS_SHOWN} of {pending.length} pending papers.{" "}
                <Link to={`/admin/papers?status=${encodeURIComponent(STATUS.PENDING)}${inDepartment}`} className="font-medium text-brand hover:underline">
                  See all
                </Link>
              </p>
            )}
          </>
        )}
      </SectionCard>

      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-2">
        <SectionCard icon={FileText} title="Recent Submissions" viewAllTo={`/admin/papers${department ? `?department=${encodeURIComponent(department)}` : ""}`}>
          {papers.loading && !papers.data ? (
            <div className="py-10 text-center">
              <Spinner label="Loading papers..." />
            </div>
          ) : (
            <RecentSubmissionsTable papers={recent} onView={(paper) => setViewId(paper.id)} />
          )}
        </SectionCard>

        <SectionCard icon={ChartNoAxesColumn} title="Department-wise Papers" viewAllTo="/admin/departments">
          {stats.loading && !stats.data ? (
            <div className="py-10 text-center">
              <Spinner label="Loading..." />
            </div>
          ) : (
            <DepartmentSummary rows={counts?.departments || []} />
          )}
        </SectionCard>
      </div>

      {viewId && <PaperViewModal paperId={viewId} onClose={() => setViewId(null)} />}
      {reviewId && <PaperReviewModal paperId={reviewId} onClose={() => setReviewId(null)} onDecided={onDecided} onChanged={refresh} />}
    </div>
  );
}
