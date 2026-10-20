import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { useLoad } from "../../lib/useLoad";
import PaperDocument from "../paper/PaperDocument";
import Alert from "../ui/Alert";
import { buttonClasses } from "../ui/buttonStyles";
import Modal from "../ui/Modal";
import Spinner from "../ui/Spinner";
import StatusBadge from "../ui/StatusBadge";

/** A quick, read-only look at one of the faculty's papers (the eye button in the tables). */
export default function PaperQuickView({ paperId, onClose }) {
  const { data: paper, error, loading } = useLoad(() => api.papers.get(paperId), paperId);
  const editable = paper && (paper.status === "Draft" || paper.status === "Rejected");

  return (
    <Modal
      open
      onClose={onClose}
      size="xl"
      title={paper ? `${paper.course_name} (${paper.course_code})` : "Question paper"}
      subtitle={paper ? `${paper.exam_type === "MSE" ? "Mid Semester" : "End Semester"} Examination` : undefined}
      footer={
        paper && (
          <>
            <StatusBadge status={paper.status} className="mr-auto" />
            <Link to={`/faculty/papers/${paper.id}`} className={buttonClasses({ variant: "primary" })}>
              {editable ? "Open and edit" : "Open full page"}
            </Link>
          </>
        )
      }
    >
      {loading && <Spinner label="Loading the paper..." />}
      {error && <Alert tone="error">{error.message}</Alert>}
      {paper && (
        <div className="space-y-4">
          {paper.status === "Rejected" && paper.rejection_reason && (
            <Alert tone="error" title="Rejected by the admin">
              {paper.rejection_reason}
            </Alert>
          )}
          <PaperDocument paper={paper} showAnswers />
        </div>
      )}
    </Modal>
  );
}
