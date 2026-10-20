import { useEffect, useState } from "react";
import { listSavedSyllabi } from "../api";

export function UserDashboard({ goTo, userSession, onSelectPaper, onLogout }) {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    // Load saved papers from MongoDB and any locally cached generated papers
    async function loadDashboardData() {
      try {
        const syllabi = await listSavedSyllabi();
        if (isMounted) {
          // Transform syllabi/papers for clean display
          const storedPapers = JSON.parse(
            localStorage.getItem("blindpaper_recent_papers") || "[]"
          );

          // Merge MongoDB records with any recently generated papers
          const combined = [...storedPapers];
          if (syllabi && Array.isArray(syllabi)) {
            syllabi.forEach((s) => {
              if (!combined.some((p) => p.id === s.id)) {
                combined.push({
                  id: s.id,
                  subject_name: s.subject_name,
                  filename: s.filename,
                  date: s.updated_at || s.created_at,
                  questions_count: s.unit_count ? s.unit_count * 2 : 5,
                  total_marks: 25,
                  status: s.processing_status === "reviewed" ? "Approved" : "Need Review",
                });
              }
            });
          }

          setPapers(combined);
          setLoading(false);
        }
      } catch {
        if (isMounted) {
          const storedPapers = JSON.parse(
            localStorage.getItem("blindpaper_recent_papers") || "[]"
          );
          setPapers(storedPapers);
          setLoading(false);
        }
      }
    }

    loadDashboardData();
    return () => {
      isMounted = false;
    };
  }, []);

  const totalGenerated = papers.length;
  const approvedCount = papers.filter((p) => p.status === "Approved").length;
  const needReviewCount = papers.filter((p) => p.status === "Need Review").length;

  return (
    <div className="user-dashboard-wrapper">
      {/* Simple Top Navigation */}
      <header className="user-dash-nav">
        <div className="user-dash-brand">
          <span className="brand-mark">B</span>
          <span className="brand-name">BlindPaper</span>
        </div>

        <div className="user-dash-profile">
          <span className="user-email">
            👤 {userSession?.email || "user@example.com"}
          </span>
          <button className="dash-logout-btn" onClick={onLogout} type="button">
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Dashboard Container */}
      <div className="user-dash-content">
        <div className="user-dash-header">
          <div>
            <h1>Dashboard</h1>
            <p>Overview of your generated question papers and assessments.</p>
          </div>

          <button
            className="primary-button create-paper-btn"
            onClick={() => goTo("upload_pdf")}
            type="button"
          >
            + Create New Paper
          </button>
        </div>

        {/* 4 Summary Cards */}
        <div className="dash-summary-grid">
          {/* Card 1: Total Papers Generated */}
          <div className="dash-stat-card">
            <div className="stat-card-top">
              <span className="stat-card-title">Total Papers Generated</span>
              <span className="stat-card-icon">📄</span>
            </div>
            <div className="stat-card-value">
              {loading ? "..." : totalGenerated}
            </div>
            <span className="stat-card-sub">All-time question papers</span>
          </div>

          {/* Card 2: Create New Paper Component */}
          <div
            className="dash-stat-card action-card"
            onClick={() => goTo("upload_pdf")}
          >
            <div className="stat-card-top">
              <span className="stat-card-title">Create New Paper</span>
              <span className="stat-card-icon action-icon">➕</span>
            </div>
            <div className="action-card-text">
              Upload syllabus PDF to configure a new paper
            </div>
            <button
              className="action-card-button"
              onClick={(e) => {
                e.stopPropagation();
                goTo("upload_pdf");
              }}
              type="button"
            >
              Upload PDF →
            </button>
          </div>

          {/* Card 3: Approved Paper */}
          <div className="dash-stat-card">
            <div className="stat-card-top">
              <span className="stat-card-title">Approved Papers</span>
              <span className="stat-card-icon approved-icon">✓</span>
            </div>
            <div className="stat-card-value text-success">
              {loading ? "..." : approvedCount}
            </div>
            <span className="stat-card-sub">Validated & ready papers</span>
          </div>

          {/* Card 4: Need Review */}
          <div className="dash-stat-card">
            <div className="stat-card-top">
              <span className="stat-card-title">Need Review</span>
              <span className="stat-card-icon review-icon">⚠️</span>
            </div>
            <div className="stat-card-value text-warning">
              {loading ? "..." : needReviewCount}
            </div>
            <span className="stat-card-sub">Pending verification</span>
          </div>
        </div>

        {/* Recent Papers Component */}
        <div className="recent-papers-section">
          <div className="recent-papers-header">
            <h2>Recent Papers</h2>
            <span className="recent-count">
              Showing {papers.length} paper(s)
            </span>
          </div>

          {loading ? (
            <div className="clean-loading-box">
              <div className="spinner"></div>
              <span>Loading recent papers...</span>
            </div>
          ) : papers.length === 0 ? (
            <div className="clean-empty-box">
              <span className="empty-icon">📝</span>
              <h3>No question papers yet</h3>
              <p>
                Click <strong>Create New Paper</strong> to upload a syllabus PDF and configure your first assessment.
              </p>
              <button
                className="primary-button"
                onClick={() => goTo("upload_pdf")}
                type="button"
              >
                + Create New Paper
              </button>
            </div>
          ) : (
            <div className="clean-table-card">
              <table className="clean-papers-table">
                <thead>
                  <tr>
                    <th>Subject / Course</th>
                    <th>Date</th>
                    <th>Details</th>
                    <th>Status</th>
                    <th className="table-actions-col">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {papers.map((p, idx) => (
                    <tr key={p.id || idx}>
                      <td>
                        <strong>{p.subject_name || "Untitled Course"}</strong>
                        {p.filename && (
                          <span className="table-filename">{p.filename}</span>
                        )}
                      </td>
                      <td className="table-date">
                        {p.date
                          ? new Date(p.date).toLocaleDateString()
                          : "Recently"}
                      </td>
                      <td>
                        <span className="details-chip">
                          {p.questions_count || 5} Questions • {p.total_marks || 25} Marks
                        </span>
                      </td>
                      <td>
                        <span
                          className={`clean-status-pill ${
                            p.status === "Approved"
                              ? "pill-approved"
                              : "pill-review"
                          }`}
                        >
                          {p.status === "Approved" ? "✓ Approved" : "Need Review"}
                        </span>
                      </td>
                      <td className="table-actions-col">
                        <button
                          className="table-action-btn"
                          onClick={() => {
                            if (onSelectPaper) onSelectPaper(p);
                            goTo("paper_config");
                          }}
                          type="button"
                        >
                          Configure Paper →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
