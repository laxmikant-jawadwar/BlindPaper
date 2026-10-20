import { useEffect, useState } from "react";
import { listSavedSyllabi, getSyllabusById, deleteSyllabusFromDb } from "../api";

export function FacultyDashboard({
  goTo,
  onSelectSyllabus,
  onEditSyllabusStructure,
  dbStatus,
}) {
  const [syllabi, setSyllabi] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const fetchSyllabi = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSavedSyllabi();
      setSyllabi(data);
    } catch (err) {
      setError(err.message || "Failed to load saved syllabi from database.");
    } finally {
      setLoading(false);
    }
  };

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
          setError(err.message || "Failed to load saved syllabi from database.");
          setLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleStartPaper = async (syllabusId) => {
    try {
      setLoading(true);
      const fullDoc = await getSyllabusById(syllabusId);
      onSelectSyllabus(fullDoc);
      goTo("paper_config");
    } catch (err) {
      setError(`Failed to open syllabus: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewStructure = async (syllabusId) => {
    try {
      setLoading(true);
      const fullDoc = await getSyllabusById(syllabusId);
      onEditSyllabusStructure(fullDoc);
      goTo("syllabus_review");
    } catch (err) {
      setError(`Failed to open syllabus for review: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (syllabusId, subjectName) => {
    if (
      !window.confirm(
        `Are you sure you want to delete the syllabus for "${subjectName}"?`
      )
    ) {
      return;
    }

    try {
      setDeletingId(syllabusId);
      await deleteSyllabusFromDb(syllabusId);
      setSyllabi((prev) => prev.filter((s) => s.id !== syllabusId));
    } catch (err) {
      setError(`Failed to delete syllabus: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <span className="eyebrow">FACULTY PORTAL</span>
          <h1>Question Paper Studio</h1>
          <p className="dashboard-subtitle">
            Create, validate, and export syllabus-grounded examination papers
            aligned with Bloom's Taxonomy.
          </p>
        </div>

        <div className="dashboard-header-actions">
          <button
            className="primary-button hero-button"
            onClick={() => goTo("create_paper")}
            type="button"
          >
            <span>+</span> Create Question Paper
          </button>
        </div>
      </div>

      <div className="system-status-bar">
        <div className="status-item">
          <span className="status-label">Database Persistence:</span>
          <span
            className={`status-chip ${
              dbStatus === "connected" ? "chip-success" : "chip-warning"
            }`}
          >
            {dbStatus === "connected" ? "● MongoDB Local Connected" : "○ MongoDB Unchecked"}
          </span>
        </div>
        <div className="status-item">
          <span className="status-label">Saved Syllabi:</span>
          <span className="status-count">{syllabi.length} Document(s)</span>
        </div>
        <button
          className="refresh-btn"
          onClick={fetchSyllabi}
          title="Refresh syllabus list"
          type="button"
        >
          ↻ Refresh
        </button>
      </div>

      {error && (
        <div className="alert-box alert-error">
          <span className="alert-icon">⚠️</span>
          <div className="alert-body">
            <strong>Error loading data</strong>
            <p>{error}</p>
          </div>
          <button className="retry-btn" onClick={fetchSyllabi} type="button">
            Try Again
          </button>
        </div>
      )}

      <div className="syllabus-section">
        <div className="section-title-row">
          <h2>Saved Syllabi in MongoDB</h2>
          <span className="section-hint">
            Select a saved syllabus to create a new paper or upload a new one.
          </span>
        </div>

        {loading ? (
          <div className="loading-card">
            <div className="spinner"></div>
            <p>Loading course syllabi from MongoDB...</p>
          </div>
        ) : syllabi.length === 0 ? (
          <div className="empty-state-card">
            <div className="empty-icon">📄</div>
            <h3>No Syllabi Saved Yet</h3>
            <p>
              Upload your course syllabus PDF to begin. The system will extract
              its text, recommend Bloom's Taxonomy cognitive levels, and persist
              the confirmed structure in MongoDB.
            </p>
            <button
              className="primary-button"
              onClick={() => goTo("create_paper")}
              type="button"
            >
              Upload First Syllabus PDF
            </button>
          </div>
        ) : (
          <div className="syllabi-grid">
            {syllabi.map((s) => (
              <div key={s.id} className="syllabus-card">
                <div className="syllabus-card-header">
                  <div className="subject-icon">📚</div>
                  <div>
                    <h3 className="subject-title">{s.subject_name}</h3>
                    <span className="filename-tag">{s.filename}</span>
                  </div>
                </div>

                <div className="syllabus-meta-row">
                  <div className="meta-badge">
                    <strong>{s.unit_count}</strong> Units
                  </div>
                  <div className="meta-badge">
                    <strong>{s.page_count}</strong> Page(s)
                  </div>
                  <div className="status-badge reviewed">
                    {s.processing_status}
                  </div>
                </div>

                <div className="syllabus-timestamps">
                  <span>Saved: {s.created_at ? new Date(s.created_at).toLocaleDateString() : "Recently"}</span>
                  {s.updated_at && (
                    <span>
                      Updated: {new Date(s.updated_at).toLocaleDateString()}
                    </span>
                  )}
                </div>

                <div className="syllabus-card-actions">
                  <button
                    className="primary-button full-button"
                    onClick={() => handleStartPaper(s.id)}
                    type="button"
                  >
                    Create Paper →
                  </button>
                  <div className="card-sub-actions">
                    <button
                      className="text-button"
                      onClick={() => handleReviewStructure(s.id)}
                      type="button"
                    >
                      ✏️ Review Structure
                    </button>
                    <button
                      className="text-button text-danger"
                      onClick={() => handleDelete(s.id, s.subject_name)}
                      disabled={deletingId === s.id}
                      type="button"
                    >
                      {deletingId === s.id ? "Deleting..." : "🗑️ Delete"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
