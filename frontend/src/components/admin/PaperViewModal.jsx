import { Download } from "lucide-react";
import { api } from "../../api/client";
import PaperDocument from "../paper/PaperDocument";
import Alert from "../ui/Alert";
import Button from "../ui/Button";
import Modal from "../ui/Modal";
import Spinner from "../ui/Spinner";
import PaperDetails from "./PaperDetails";
import { useLoad } from "../../lib/useLoad";
import { usePdfDownload } from "./usePdfDownload";

/** Workflow step 9: open a submitted paper and read it, with its details. Nothing can be decided here. */
export default function PaperViewModal({ paperId, onClose }) {
  const { data: paper, error, loading } = useLoad(() => api.admin.paper(paperId), [paperId]);
  const pdf = usePdfDownload();

  return (
    <Modal
      open
      onClose={onClose}
      size="xl"
      title={paper ? paper.course_name : "Question paper"}
      subtitle={paper ? `${paper.course_code} · ${paper.faculty_name}` : undefined}
      footer={
        <>
          {paper && (
            <Button variant="outline" loading={pdf.busyId === paper.id} onClick={() => pdf.download(paper)}>
              <Download className="size-4" aria-hidden="true" /> Download PDF
            </Button>
          )}
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </>
      }
    >
      {loading && !paper && <Spinner label="Loading the paper..." />}
      {error && <Alert tone="error">{error.message}</Alert>}
      {pdf.error && (
        <Alert tone="error" className="mb-4">
          Could not download the PDF: {pdf.error}
        </Alert>
      )}
      {paper && (
        <div className="space-y-6">
          <PaperDetails paper={paper} />
          <PaperDocument paper={paper} showAnswers />
        </div>
      )}
    </Modal>
  );
}
