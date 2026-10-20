import { useState } from "react";
import { processSyllabus } from "../api";

export function UploadPdf({ goTo, onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(null);

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

  const handleProcess = async () => {
    if (!file) {
      setError("Please choose a syllabus PDF file to upload.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      setSaved(await processSyllabus(file));
    } catch (err) {
      setError(err.message || "Failed to process the syllabus PDF.");
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => {
    onUploadComplete({
      syllabus_id: saved.id,
      subject_name: saved.subject_name,
      filename: saved.filename,
      extracted_text: saved.extracted_text,
      units: saved.course_content.map(
        (unit) => `Unit ${unit.unit_number}: ${unit.unit_name}`
      ),
    });
    goTo("paper_config");
  };

  const handleUploadAnother = () => {
    setSaved(null);
    setFile(null);
    setError(null);
  };

  const header = (
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
  );

  if (saved) {
    const units = saved.course_content ?? [];
    const outcomes = saved.course_outcomes ?? [];
    const needsReview = saved.processing_status === "extracted";

    return (
      <div className="clean-page-wrapper">
        {header}

        <div className="clean-card">
          <div className="clean-card-title-group">
            <h1>Syllabus saved</h1>
            <p>
              The extracted text and the structured syllabus are stored together
              under one syllabus ID.
            </p>
          </div>

          {needsReview ? (
            <div className="clean-alert-warning">
              <span>
                ⚠️ No unit headings were found in this PDF, so the course
                contents could not be structured. The text is saved, but you
                can&apos;t configure a paper from it yet.
              </span>
            </div>
          ) : (
            <div className="clean-alert-success">
              <span>
                ✓ Found {units.length} unit{units.length === 1 ? "" : "s"} and{" "}
                {outcomes.length} course outcome
                {outcomes.length === 1 ? "" : "s"} in {saved.filename} and saved
                it to the database.
              </span>
            </div>
          )}

          <dl className="syllabus-meta-grid">
            <div>
              <dt>Course name</dt>
              <dd>{saved.subject_name}</dd>
            </div>
            <div>
              <dt>Course code</dt>
              <dd>{saved.course_code || "—"}</dd>
            </div>
            <div>
              <dt>File</dt>
              <dd>{saved.filename}</dd>
            </div>
            <div>
              <dt>Pages</dt>
              <dd>{saved.page_count}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <span
                  className={`clean-status-pill ${
                    needsReview ? "pill-review" : "pill-approved"
                  }`}
                >
                  {needsReview ? "Needs review" : "Structured"}
                </span>
              </dd>
            </div>
            <div>
              <dt>Syllabus ID</dt>
              <dd className="syllabus-id">{saved.id}</dd>
            </div>
          </dl>

          {saved.course_description && (
            <section className="syllabus-section">
              <h2>Course description</h2>
              <p className="syllabus-description">{saved.course_description}</p>
            </section>
          )}

          {outcomes.length > 0 && (
            <section className="syllabus-section">
              <h2>Course outcomes</h2>
              <ul className="syllabus-outcomes">
                {outcomes.map((outcome) => (
                  <li key={outcome.code}>
                    <span className="outcome-code">{outcome.code}</span>
                    <span className="outcome-text">{outcome.description}</span>
                    {outcome.blooms_descriptor && (
                      <span
                        className="blooms-tag"
                        title={
                          outcome.blooms_level
                            ? `Bloom's level ${outcome.blooms_level}`
                            : undefined
                        }
                      >
                        {outcome.blooms_descriptor}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {units.length > 0 && (
            <section className="syllabus-section">
              <h2>Course contents</h2>
              <div className="syllabus-units">
                {units.map((unit, idx) => (
                  <details
                    className="syllabus-unit"
                    key={`${unit.unit_number}-${unit.unit_name}`}
                    open={idx === 0}
                  >
                    <summary>
                      <span className="syllabus-unit-name">
                        Unit {unit.unit_number}: {unit.unit_name}
                      </span>
                      <span className="syllabus-unit-meta">
                        <span className="details-chip">
                          {unit.topics.length} topic
                          {unit.topics.length === 1 ? "" : "s"}
                        </span>
                      </span>
                    </summary>
                    <div className="syllabus-topics">
                      {unit.topics.map((topic, topicIdx) => (
                        <span className="topic-chip" key={topicIdx}>
                          {topic}
                        </span>
                      ))}
                    </div>
                  </details>
                ))}
              </div>
            </section>
          )}

          <div className="clean-actions-row">
            <button
              className="primary-button"
              onClick={handleContinue}
              disabled={units.length === 0}
              type="button"
            >
              Continue to Paper Configuration →
            </button>

            <button
              className="secondary-button"
              onClick={handleUploadAnother}
              type="button"
            >
              Upload another PDF
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="clean-page-wrapper">
      {header}

      <div className="clean-card">
        <div className="clean-card-title-group">
          <h1>Upload Syllabus PDF</h1>
          <p>
            Upload your syllabus PDF. It is read, split into course outcomes and
            units with topics, and saved to the database.
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
            <span>Reading, structuring and saving your syllabus...</span>
          </div>
        )}

        <div className="clean-actions-row">
          <button
            className="primary-button"
            onClick={handleProcess}
            disabled={!file || loading}
            type="button"
          >
            {loading ? "Processing..." : "Upload & Process →"}
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
