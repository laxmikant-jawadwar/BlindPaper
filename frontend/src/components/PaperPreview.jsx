import { useState } from "react";
import { exportQuestionPaperPdf } from "../api";

export function PaperPreview({
  goTo,
  config,
  questions,
  onResetWorkflow,
}) {
  const [downloading, setDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(null);
  const [downloadError, setDownloadError] = useState(null);

  const totalMarks = questions.reduce((sum, q) => sum + (Number(q.marks) || 0), 0);

  const handleExportPdf = async () => {
    setDownloading(true);
    setDownloadError(null);
    setDownloadSuccess(null);

    const payload = {
      subject_name: config.subject_name,
      questions: questions,
      total_marks: totalMarks,
      question_count: questions.length,
      college_name: config.college_name || undefined,
      exam_name: config.exam_name || undefined,
      semester: config.semester || undefined,
      paper_code: config.paper_code || undefined,
      duration: config.duration || undefined,
      instructions: config.instructions || undefined,
    };

    try {
      const { blob, filename } = await exportQuestionPaperPdf(payload);

      // Create browser blob URL and trigger download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setDownloadSuccess(`Successfully downloaded "${filename}"!`);
    } catch (err) {
      setDownloadError(err.message || "Failed to download PDF question paper.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="workflow-container">
      <div className="workflow-breadcrumbs">
        <button
          className="breadcrumb-btn"
          onClick={() => goTo("question_review")}
          type="button"
        >
          ← Back to Question Review
        </button>
        <span className="breadcrumb-step">Final Preview & PDF Export</span>
      </div>

      <div className="workflow-card">
        {/* Actions Bar on Top */}
        <div className="preview-top-actions">
          <div>
            <span className="card-eyebrow">FINAL DOCUMENT</span>
            <h2>Examination Paper Preview</h2>
          </div>

          <div className="preview-cta-buttons">
            <button
              type="button"
              className="primary-button hero-button export-btn"
              onClick={handleExportPdf}
              disabled={downloading}
            >
              {downloading ? (
                <span className="button-spinner-row">
                  <span className="spinner"></span>
                  Exporting PDF...
                </span>
              ) : (
                "📥 Export & Download PDF"
              )}
            </button>
          </div>
        </div>

        {downloadSuccess && (
          <div className="alert-box alert-success">
            <span className="alert-icon">✓</span>
            <div className="alert-body">
              <strong>Download Complete!</strong>
              <p>{downloadSuccess}</p>
            </div>
            <button
              className="action-btn"
              onClick={onResetWorkflow}
              type="button"
            >
              Start Another Paper
            </button>
          </div>
        )}

        {downloadError && (
          <div className="alert-box alert-error">
            <span className="alert-icon">⚠️</span>
            <div className="alert-body">
              <strong>Export Issue</strong>
              <p>{downloadError}</p>
            </div>
          </div>
        )}

        {/* Paper Document Preview Simulation */}
        <div className="paper-document-sheet">
          {/* Header */}
          <div className="sheet-header">
            {config.college_name && (
              <h1 className="sheet-college">{config.college_name}</h1>
            )}
            <h2 className="sheet-exam">{config.exam_name || "Examination Paper"}</h2>

            <div className="sheet-meta-grid">
              <div>
                <strong>Subject:</strong> {config.subject_name}
              </div>
              {config.paper_code && (
                <div>
                  <strong>Paper Code:</strong> {config.paper_code}
                </div>
              )}
              {config.semester && (
                <div>
                  <strong>Semester:</strong> {config.semester}
                </div>
              )}
              {config.duration && (
                <div>
                  <strong>Time:</strong> {config.duration}
                </div>
              )}
              <div className="sheet-max-marks">
                <strong>Max Marks:</strong> {totalMarks}
              </div>
            </div>
          </div>

          <hr className="sheet-divider" />

          {/* Instructions */}
          {config.instructions && config.instructions.length > 0 && (
            <div className="sheet-instructions">
              <strong>Instructions to Candidates:</strong>
              <ol>
                {config.instructions.map((inst, idx) => (
                  <li key={idx}>{inst}</li>
                ))}
              </ol>
            </div>
          )}

          <hr className="sheet-divider-subtle" />

          {/* Questions */}
          <div className="sheet-questions-list">
            {questions.map((q, idx) => (
              <div key={q.question_id || idx} className="sheet-question-row">
                <div className="sheet-q-num">Q{idx + 1}.</div>
                <div className="sheet-q-body">
                  <div className="sheet-q-text">{q.question_text}</div>
                  <div className="sheet-q-tags">
                    <span className="sheet-tag">[{q.unit_or_topic}]</span>
                    <span className="sheet-tag">[{q.question_type}]</span>
                    {q.blooms_level && (
                      <span className="sheet-tag bloom">[{q.blooms_level}]</span>
                    )}
                  </div>
                </div>
                <div className="sheet-q-marks">[{q.marks} Marks]</div>
              </div>
            ))}
          </div>

          {/* Footer of the sheet */}
          <div className="sheet-footer">
            <span>--- End of Question Paper ---</span>
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="workflow-footer-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => goTo("question_review")}
          >
            ← Back to Question Review
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={onResetWorkflow}
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
