import { useEffect, useState } from "react";
import { listSavedSyllabi, getSyllabusById } from "../api";

export function CreatePaperChoice({
  goTo,
  onSelectSyllabus,
}) {
  const [syllabi, setSyllabi] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    listSavedSyllabi()
      .then((data) => {
        if (isMounted) {
          setSyllabi(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError("Could not load saved syllabi: " + err.message);
          setLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSelectSaved = async (id) => {
    try {
      setLoading(true);
      const fullDoc = await getSyllabusById(id);
      onSelectSyllabus(fullDoc);
      goTo("paper_config");
    } catch (err) {
      setError("Failed to load syllabus: " + err.message);
      setLoading(false);
    }
  };

  return (
    <div className="workflow-container">
      <div className="workflow-breadcrumbs">
        <button className="breadcrumb-btn" onClick={() => goTo("faculty_dashboard")} type="button">
          ← Back to Dashboard
        </button>
        <span className="breadcrumb-step">Select Workflow Method</span>
      </div>

      <div className="workflow-card">
        <div className="card-header">
          <span className="card-eyebrow">QUESTION PAPER CREATION</span>
          <h2>How would you like to start?</h2>
          <p className="card-desc">
            You can either upload a new college course syllabus PDF or pick an existing,
            already-confirmed syllabus from local MongoDB.
          </p>
        </div>

        {error && (
          <div className="alert-box alert-error">
            <span className="alert-icon">⚠️</span>
            <div className="alert-body">
              <p>{error}</p>
            </div>
          </div>
        )}

        <div className="choice-options-grid">
          {/* Option 1: Upload New */}
          <div className="choice-card" onClick={() => goTo("upload_syllabus")}>
            <div className="choice-icon-wrap">📤</div>
            <h3>Upload New Syllabus PDF</h3>
            <p>
              Upload a new college syllabus in PDF format. The system will extract
              its text, recommend Bloom's Taxonomy cognitive levels, and allow you
              to review and save it to MongoDB.
            </p>
            <button
              className="primary-button full-button"
              onClick={() => goTo("upload_syllabus")}
              type="button"
            >
              Upload PDF File →
            </button>
          </div>

          {/* Option 2: Choose from Saved */}
          <div className="choice-card">
            <div className="choice-icon-wrap">💾</div>
            <h3>Use Saved Syllabus from MongoDB</h3>
            <p>
              Choose from your confirmed course syllabi saved in local MongoDB
              without uploading the document again.
            </p>

            {loading ? (
              <div className="loading-card-mini">
                <div className="spinner"></div>
                <span>Checking MongoDB...</span>
              </div>
            ) : syllabi.length === 0 ? (
              <div className="no-saved-mini">
                <span>No saved syllabi found in MongoDB yet.</span>
                <button
                  className="secondary-button"
                  onClick={() => goTo("upload_syllabus")}
                  type="button"
                >
                  Upload First PDF
                </button>
              </div>
            ) : (
              <div className="saved-select-list">
                {syllabi.map((s) => (
                  <div
                    key={s.id}
                    className="saved-mini-item"
                    onClick={() => handleSelectSaved(s.id)}
                  >
                    <div>
                      <strong>{s.subject_name}</strong>
                      <span className="saved-mini-sub">
                        {s.unit_count} Units • {s.filename}
                      </span>
                    </div>
                    <span className="arrow-btn">Select →</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="workflow-footer-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => goTo("faculty_dashboard")}
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
