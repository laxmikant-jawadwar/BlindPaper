import { useState } from "react";
import { uploadSyllabusFile, structureSyllabusText } from "../api";

export function UploadSyllabus({ goTo, onExtractionComplete, onSelectExisting }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState("");
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    setError(null);
    if (!selected) {
      setFile(null);
      return;
    }

    if (!selected.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a valid PDF document (.pdf).");
      setFile(null);
      return;
    }

    if (selected.size > 10 * 1024 * 1024) {
      setError("File exceeds the 10 MB size limit. Please choose a smaller PDF.");
      setFile(null);
      return;
    }

    setFile(selected);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return "0 KB";
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleUploadAndExtract = async () => {
    if (!file) {
      setError("Please select a syllabus PDF file first.");
      return;
    }

    setLoading(true);
    setError(null);
    setProgressMsg("Uploading PDF and extracting text via PyMuPDF...");

    try {
      // 1. Upload & extract raw text
      const extractResult = await uploadSyllabusFile(file);

      setProgressMsg("Analyzing syllabus structure & inferring Bloom's Taxonomy levels...");

      // 2. Structure raw text into units and topics with Bloom's categorization
      const structureResult = await structureSyllabusText({
        extracted_text: extractResult.extracted_text,
        filename: extractResult.filename,
        page_count: extractResult.page_count,
      });

      // Pass structured data to parent review workflow
      onExtractionComplete({
        subject_name: structureResult.subject_name,
        filename: structureResult.filename,
        page_count: structureResult.page_count,
        extracted_text: structureResult.extracted_text,
        structured_syllabus: structureResult.structured_syllabus,
      });

      goTo("syllabus_review");
    } catch (err) {
      setError(err.message || "Failed to process syllabus PDF.");
    } finally {
      setLoading(false);
      setProgressMsg("");
    }
  };

  return (
    <div className="workflow-container">
      <div className="workflow-breadcrumbs">
        <button className="breadcrumb-btn" onClick={() => goTo("faculty_dashboard")} type="button">
          ← Back to Dashboard
        </button>
        <span className="breadcrumb-step">Step 1 of 4: Syllabus Upload</span>
      </div>

      <div className="workflow-card">
        <div className="card-header">
          <span className="card-eyebrow">COURSE SYLLABUS</span>
          <h2>Upload Syllabus PDF</h2>
          <p className="card-desc">
            Upload your course syllabus PDF (up to 10 MB). PyMuPDF will extract
            the content and our engine will structure it into units with Bloom's
            cognitive recommendations.
          </p>
        </div>

        {error && (
          <div className="alert-box alert-error">
            <span className="alert-icon">⚠️</span>
            <div className="alert-body">
              <strong>Upload or Extraction Issue</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        <div className="upload-dropzone">
          <input
            type="file"
            id="syllabus-file-input"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            disabled={loading}
            className="file-input-hidden"
          />
          <label htmlFor="syllabus-file-input" className="file-input-label">
            <div className="dropzone-icon">📥</div>
            <strong>Click to browse or choose PDF file</strong>
            <span>Maximum file size: 10 MB • Text-based PDF required</span>
          </label>
        </div>

        {file && (
          <div className="selected-file-card">
            <div className="file-info-group">
              <span className="file-icon">📄</span>
              <div className="file-details">
                <strong>{file.name}</strong>
                <span>{formatFileSize(file.size)}</span>
              </div>
            </div>
            <button
              className="remove-file-btn"
              onClick={() => setFile(null)}
              disabled={loading}
              type="button"
            >
              ✕ Remove
            </button>
          </div>
        )}

        {loading && (
          <div className="progress-banner">
            <div className="spinner"></div>
            <span>{progressMsg}</span>
          </div>
        )}

        <div className="upload-actions-row">
          <button
            className="primary-button"
            onClick={handleUploadAndExtract}
            disabled={!file || loading}
            type="button"
          >
            {loading ? "Processing..." : "Extract & Structure Syllabus →"}
          </button>

          <button
            className="secondary-button"
            onClick={() => goTo("faculty_dashboard")}
            disabled={loading}
            type="button"
          >
            Cancel
          </button>

          <button
            className="text-button select-saved-link"
            onClick={onSelectExisting}
            disabled={loading}
            type="button"
          >
            Or select from previously saved syllabi →
          </button>
        </div>

        <div className="upload-notes">
          <h4>💡 Guidelines & Limitations:</h4>
          <ul>
            <li>
              <strong>Text-based PDFs:</strong> Ensure the PDF contains readable
              text. Scanned/image-only PDFs require OCR which is currently not
              supported.
            </li>
            <li>
              <strong>Unit Headings:</strong> Documents with standard headings
              (e.g., "Unit 1", "Module I") will be structured automatically.
            </li>
            <li>
              <strong>Faculty Review:</strong> You will review, edit, and confirm
              all units and Bloom's classifications on the next screen before
              saving to MongoDB.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
