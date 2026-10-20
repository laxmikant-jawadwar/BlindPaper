import { Check, Clock, FilePlus2, FileText, Plus } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api, saveBlob } from "../../api/client";
import { useAuth } from "../../auth/authContext";
import PaperQuickView from "../../components/papers/PaperQuickView";
import PapersTable from "../../components/papers/PapersTable";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import { buttonClasses } from "../../components/ui/buttonStyles";
import EmptyState from "../../components/ui/EmptyState";
import PageHeading from "../../components/ui/PageHeading";
import Spinner from "../../components/ui/Spinner";
import StatCard from "../../components/ui/StatCard";
import { useLoad } from "../../lib/useLoad";

const RECENT = 5;

export default function Dashboard() {
  const { user } = useAuth();
  const { data: papers, loading, error, reload } = useLoad(() => api.papers.list());
  const [quickView, setQuickView] = useState(null);
  const [downloadError, setDownloadError] = useState(null);

  const all = papers || [];
  const count = (status) => all.filter((p) => p.status === status).length;

  const download = async (paper) => {
    setDownloadError(null);
    try {
      saveBlob(await api.papers.pdf(paper.id));
    } catch (err) {
      setDownloadError(err.message);
    }
  };

  return (
    <>
      <PageHeading
        title={
          <>
            Welcome, {user.name} <span aria-hidden="true">👋</span>
          </>
        }
        subtitle="Generate syllabus-based question papers using AI."
      />

      <div className="grid gap-5 md:grid-cols-3">
        <StatCard tone="blue" icon={FileText} value={loading && !papers ? "–" : all.length} label="Total Papers" />
        <StatCard tone="orange" icon={Clock} value={loading && !papers ? "–" : count("Pending Approval")} label="Pending Approval" />
        <StatCard tone="green" icon={Check} value={loading && !papers ? "–" : count("Approved")} label="Approved" />
      </div>

      <section className="mt-6 rounded-xl border border-slate-100 bg-white p-6 shadow-sm" aria-labelledby="my-papers-heading">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <h2 id="my-papers-heading" className="text-2xl font-bold text-ink">
            My Papers
          </h2>
          <div className="flex items-center gap-4">
            {all.length > RECENT && (
              <Link to="/faculty/papers" className="text-sm font-semibold text-brand hover:underline">
                View All →
              </Link>
            )}
            <Link to="/faculty/generate" className={buttonClasses({ variant: "primary", size: "lg" })}>
              <Plus className="size-5" aria-hidden="true" />
              Generate New Paper
            </Link>
          </div>
        </div>

        {downloadError && <Alert tone="error" className="mb-4">{downloadError}</Alert>}
        {error && (
          <Alert tone="error" title="Could not load your papers">
            {error.message}{" "}
            <Button variant="ghost" size="sm" onClick={reload}>
              Try again
            </Button>
          </Alert>
        )}
        {loading && !papers && <Spinner label="Loading your papers..." />}
        {papers && all.length === 0 && (
          <EmptyState icon={FilePlus2} title="You have not generated any papers yet">
            Upload a syllabus and configure your first question paper. It will appear here.
          </EmptyState>
        )}
        {all.length > 0 && <PapersTable papers={all.slice(0, RECENT)} onQuickView={setQuickView} onDownload={download} />}
      </section>

      {quickView && <PaperQuickView paperId={quickView} onClose={() => setQuickView(null)} />}
    </>
  );
}
