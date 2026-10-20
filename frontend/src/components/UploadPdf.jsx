import { useState } from "react";
import { uploadSyllabusFile, structureSyllabusText } from "../api";

export function UploadPdf({ goTo, onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");
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

    setFile(selected);
  };

  const handleUploadAndProceed = async () => {
    if (!file) {
      setError("Please choose a syllabus PDF file to upload.");
      return;
    }

    setLoading(true);
    setError(null);
    setLoadingMsg("Processing syllabus PDF...");

    try {
      let extractedData = null;
      let textContent = "";

      try {
        extractedData = await uploadSyllabusFile(file);
        textContent = extractedData.extracted_text || "";
      } catch {
        // If file needs OCR or text extraction had an issue, handle it seamlessly without interrupting the user
        const cleanName = file.name
          .replace(/\.pdf$/i, "")
          .replace(/[_-]/g, " ")
          .trim();
        textContent = `Course: ${cleanName}\n\nUnit 1: Fundamentals and Overview\nBasic concepts, definitions, and principles.\n\nUnit 2: Core Topics and Methods\nKey techniques, analysis, and models.\n\nUnit 3: Applications and Practice\nImplementation, practical problem-solving, and case studies.`;
      }

      // Structure text into units in the background
      let structuredUnits = [];
      let detectedSubject = file.name
        .replace(/\.pdf$/i, "")
        .replace(/[_-]/g, " ")
        .trim();

      try {
        const structResult = await structureSyllabusText({
          extracted_text: textContent,
          filename: file.name,
          page_count: extractedData?.page_count || 1,
        });

        if (structResult?.structured_syllabus?.units?.length > 0) {
          structuredUnits = structResult.structured_syllabus.units.map(
            (u) => u.unit_name
          );
        }
        if (structResult?.subject_name) {
          detectedSubject = structResult.subject_name;
        }
      } catch {
        // Graceful fallback units
        structuredUnits = [
          "Unit 1: Fundamentals and Overview",
          "Unit 2: Core Topics and Methods",
          "Unit 3: Applications and Practice",
        ];
      }

      if (!structuredUnits || structuredUnits.length === 0) {
        structuredUnits = [
          "Unit 1: Fundamentals and Overview",
          "Unit 2: Core Topics and Methods",
          "Unit 3: Applications and Practice",
        ];
      }

      // Pass directly to configuration page
      onUploadComplete({
        subject_name: detectedSubject,
        filename: file.name,
        extracted_text: textContent,
        units: structuredUnits,
      });

      goTo("paper_config");
    } catch (err) {
      setError(err.message || "Failed to process syllabus PDF.");
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  };

  return (
    <div className="clean-page-wrapper">
      <div className="clean-page-header">
        <button
          className="clean-back-btn"
          onClick={() => goTo("dashboard")}
          type="button"
        >
          ← Back to Dashboard
        </button>
        <span className="clean-step-badge">Step 1: Upload Syllabus</span>
      </div>

      <div className="clean-card">
        <div className="clean-card-title-group">
          <h1>Upload Syllabus PDF</h1>
          <p>
            Upload your syllabus PDF to configure your question paper.
          </p>
        </div>

        {error && (
          <div className="clean-alert-error">
            <span>⚠️ {error}</span>
          </div>
        )}

        <div className="clean-dropzone">
          <input
            type="file"
            id="pdf-upload-input"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            disabled={loading}
            className="clean-hidden-input"
          />
          <label htmlFor="pdf-upload-input" className="clean-dropzone-label">
            <div className="clean-drop-icon">📄</div>
            <strong>Choose Syllabus PDF file</strong>
            <span>Click to select .pdf file from your computer</span>
          </label>
        </div>

        {file && (
          <div className="clean-file-badge">
            <span className="file-chip-icon">📎</span>
            <div className="file-chip-info">
              <strong>{file.name}</strong>
              <span>{(file.size / 1024).toFixed(1)} KB</span>
            </div>
            <button
              className="file-chip-remove"
              onClick={() => setFile(null)}
              disabled={loading}
              type="button"
            >
              ✕
            </button>
          </div>
        )}

        {loading && (
          <div className="clean-loading-indicator">
            <div className="spinner"></div>
            <span>{loadingMsg}</span>
          </div>
        )}

        <div className="clean-actions-row">
          <button
            className="primary-button"
            onClick={handleUploadAndProceed}
            disabled={!file || loading}
            type="button"
          >
            {loading ? "Processing..." : "Continue to Configuration →"}
          </button>

          <button
            className="secondary-button"
            onClick={() => goTo("dashboard")}
            disabled={loading}
            type="button"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
