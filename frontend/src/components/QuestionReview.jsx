import { useState } from "react";
import { validateQuestionPaper } from "../api";

export function QuestionReview({
  goTo,
  syllabus,
  config,
  questions,
  generationMode,
  generationMessage,
  initialValidationReport,
  onQuestionsUpdated,
}) {
  const [questionList, setQuestionList] = useState(questions || []);
  const [validationReport, setValidationReport] = useState(
    initialValidationReport || null
  );
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState(null);
  const [showDetailedReport, setShowDetailedReport] = useState(false);

  // Live total marks calculation
  const currentTotalMarks = questionList.reduce(
    (sum, q) => sum + (Number(q.marks) || 0),
    0
  );
  const targetTotalMarks = Number(config.total_marks);
  const currentQuestionCount = questionList.length;
  const targetQuestionCount = Number(config.question_count);

  const marksMatch = currentTotalMarks === targetTotalMarks;
  const countMatch = currentQuestionCount === targetQuestionCount;

  // Question editing handlers
  const handleQuestionTextChange = (index, newText) => {
    setQuestionList((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], question_text: newText };
      onQuestionsUpdated(copy);
      return copy;
    });
  };

  const handleMarksChange = (index, newMarks) => {
    const val = Math.max(1, parseInt(newMarks, 10) || 1);
    setQuestionList((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], marks: val };
      onQuestionsUpdated(copy);
      return copy;
    });
  };

  const handleTypeChange = (index, newType) => {
    setQuestionList((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], question_type: newType };
      onQuestionsUpdated(copy);
      return copy;
    });
  };

  const handleUnitChange = (index, newUnit) => {
    setQuestionList((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], unit_or_topic: newUnit };
      onQuestionsUpdated(copy);
      return copy;
    });
  };

  const handleDeleteQuestion = (index) => {
    if (questionList.length <= 1) {
      alert("A question paper must have at least one question.");
      return;
    }
    const updated = questionList.filter((_, i) => i !== index);
    // Re-index remaining questions
    const reindexed = updated.map((q, idx) => ({ ...q, question_id: idx + 1 }));
    setQuestionList(reindexed);
    onQuestionsUpdated(reindexed);
  };

  const handleAddQuestion = () => {
    const nextId = questionList.length + 1;
    const defaultUnit = config.selected_units?.[0] || "General Topic";
    const newQuestion = {
      question_id: nextId,
      question_text: "New examination question text...",
      question_type: "Short Answer",
      unit_or_topic: defaultUnit,
      marks: 5,
      difficulty: "medium",
      blooms_level: "Understand",
    };
    const updated = [...questionList, newQuestion];
    setQuestionList(updated);
    onQuestionsUpdated(updated);
  };

  // Re-run validation API
  const handleRerunValidation = async () => {
    setValidating(true);
    setError(null);
    try {
      const report = await validateQuestionPaper({
        subject_name: config.subject_name,
        syllabus_text: syllabus.extracted_text,
        selected_units: config.selected_units,
        questions: questionList,
        total_marks: targetTotalMarks,
        question_count: targetQuestionCount,
      });
      setValidationReport(report);
    } catch (err) {
      setError(`Validation failed: ${err.message}`);
    } finally {
      setValidating(false);
    }
  };

  // Check if blocking issues prevent export
  const hasBlockingFailures =
    !marksMatch || !countMatch || validationReport?.overall_status === "fail";

  const handleProceedToPreview = () => {
    if (hasBlockingFailures) {
      if (!marksMatch) {
        setError(
          `Marks mismatch! Current total is ${currentTotalMarks} marks, but required total is ${targetTotalMarks} marks. Please adjust marks before previewing.`
        );
        return;
      }
      if (!countMatch) {
        setError(
          `Question count mismatch! Current count is ${currentQuestionCount}, but required count is ${targetQuestionCount}. Please adjust questions or configuration.`
        );
        return;
      }
      if (validationReport?.overall_status === "fail") {
        setError(
          "Question paper contains blocking quality violations (e.g. out-of-syllabus content). Please resolve the issues above before proceeding."
        );
        return;
      }
    }
    onQuestionsUpdated(questionList);
    goTo("paper_preview");
  };

  return (
    <div className="workflow-container">
      <div className="workflow-breadcrumbs">
        <button
          className="breadcrumb-btn"
          onClick={() => goTo("paper_config")}
          type="button"
        >
          ← Back to Configuration
        </button>
        <span className="breadcrumb-step">Step 4 of 4: Question Review & Quality Assurance</span>
      </div>

      <div className="workflow-card">
        {/* Header */}
        <div className="card-header">
          <div className="header-badge-row">
            <span className="card-eyebrow">QUALITY ASSURANCE</span>
            <span
              className={`mode-badge ${
                generationMode === "llm" ? "mode-llm" : "mode-demo"
              }`}
            >
              {generationMode === "llm" ? "✨ AI Generated (LLM)" : "⚡ Deterministic Demo Fallback"}
            </span>
          </div>
          <h2>Review & Validate Examination Questions</h2>
          <p className="card-desc">
            {generationMessage ||
              "All questions have been evaluated against syllabus units, marks consistency, and duplicate detection."}
          </p>
        </div>

        {error && (
          <div className="alert-box alert-error">
            <span className="alert-icon">⚠️</span>
            <div className="alert-body">
              <strong>Action Needed</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* Validation Status Dashboard Banner */}
        {validationReport && (
          <div
            className={`validation-banner ${
              validationReport.overall_status === "pass"
                ? "val-pass"
                : validationReport.overall_status === "review_required"
                ? "val-review"
                : "val-fail"
            }`}
          >
            <div className="val-banner-header">
              <div className="val-badge-wrap">
                <span className="val-status-label">Engine Verdict:</span>
                <span className="val-status-badge">
                  {validationReport.overall_status === "pass"
                    ? "✓ PASSED QUALITY CRITERIA"
                    : validationReport.overall_status === "review_required"
                    ? "⚠️ REVIEW RECOMMENDED"
                    : "✕ VIOLATIONS DETECTED"}
                </span>
              </div>

              <button
                type="button"
                className="secondary-button revalidate-btn"
                onClick={handleRerunValidation}
                disabled={validating}
              >
                {validating ? "Checking..." : "↻ Re-run Quality Engine"}
              </button>
            </div>

            <p className="val-summary-text">{validationReport.summary}</p>

            {/* Quick Metrics Bar */}
            <div className="val-metrics-row">
              <div
                className={`val-metric-pill ${
                  marksMatch ? "metric-good" : "metric-bad"
                }`}
              >
                <strong>Marks:</strong> {currentTotalMarks} / {targetTotalMarks}{" "}
                {marksMatch ? "✓" : "⚠️ (Adjust Marks)"}
              </div>

              <div
                className={`val-metric-pill ${
                  countMatch ? "metric-good" : "metric-bad"
                }`}
              >
                <strong>Count:</strong> {currentQuestionCount} / {targetQuestionCount}{" "}
                {countMatch ? "✓" : "⚠️ (Adjust Count)"}
              </div>

              <div className="val-metric-pill metric-good">
                <strong>Unit Coverage:</strong>{" "}
                {validationReport.unit_coverage?.coverage_percentage}%
              </div>

              {validationReport.duplicate_pairs?.length > 0 && (
                <div className="val-metric-pill metric-bad">
                  <strong>Duplicates:</strong> {validationReport.duplicate_pairs.length} Pair(s) Flagged
                </div>
              )}
            </div>

            {/* Collapsible Detailed Report */}
            <div className="val-details-toggle">
              <button
                type="button"
                className="text-link"
                onClick={() => setShowDetailedReport(!showDetailedReport)}
              >
                {showDetailedReport
                  ? "Hide Comprehensive Quality Breakdown ▲"
                  : "View Comprehensive Quality Breakdown ▼"}
              </button>
            </div>

            {showDetailedReport && (
              <div className="val-breakdown-panel">
                {/* Issues List */}
                {validationReport.issues?.length > 0 && (
                  <div className="report-group issues-group">
                    <h4>🚨 Blocking Violations:</h4>
                    <ul>
                      {validationReport.issues.map((issue, idx) => (
                        <li key={idx}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Warnings List */}
                {validationReport.warnings?.length > 0 && (
                  <div className="report-group warnings-group">
                    <h4>⚠️ Quality Warnings:</h4>
                    <ul>
                      {validationReport.warnings.map((warn, idx) => (
                        <li key={idx}>{warn}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Duplicate Pairs */}
                {validationReport.duplicate_pairs?.length > 0 && (
                  <div className="report-group duplicates-group">
                    <h4>👯 Suspected Duplicates:</h4>
                    {validationReport.duplicate_pairs.map((pair, idx) => (
                      <div key={idx} className="dup-pair-card">
                        <strong>
                          Q{pair.question_id_1} & Q{pair.question_id_2} (Similarity:{" "}
                          {(pair.similarity_score * 100).toFixed(0)}% - {pair.match_type})
                        </strong>
                        <p>{pair.reason}</p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Unit Coverage */}
                <div className="report-group">
                  <h4>📚 Syllabus Unit Coverage:</h4>
                  <p>
                    <strong>Represented:</strong>{" "}
                    {validationReport.unit_coverage?.covered_units?.join(", ") || "None"}
                  </p>
                  {validationReport.unit_coverage?.uncovered_units?.length > 0 && (
                    <p className="text-danger">
                      <strong>Unrepresented:</strong>{" "}
                      {validationReport.unit_coverage.uncovered_units.join(", ")}
                    </p>
                  )}
                </div>

                {/* Recommendations */}
                {validationReport.recommendations?.length > 0 && (
                  <div className="report-group recs-group">
                    <h4>💡 Actionable Recommendations:</h4>
                    <ul>
                      {validationReport.recommendations.map((rec, idx) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Questions Editor List */}
        <div className="questions-editor-section">
          <div className="editor-header-row">
            <div>
              <h3>Examination Questions ({questionList.length})</h3>
              <span className="editor-subhead">
                Edit question text, modify marks distribution, or adjust question types.
              </span>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={handleAddQuestion}
            >
              + Add Question Manually
            </button>
          </div>

          <div className="questions-stack">
            {questionList.map((q, idx) => {
              // Check if relevance findings exist for this question
              const rel = validationReport?.relevance_results?.find(
                (r) => r.question_id === q.question_id
              );

              return (
                <div key={q.question_id || idx} className="question-editor-card">
                  <div className="question-card-top-row">
                    <div className="q-number-pill">Question {idx + 1}</div>

                    <div className="q-meta-controls">
                      {/* Unit Selector */}
                      <label className="q-mini-label">
                        Unit:
                        <select
                          className="q-mini-select"
                          value={q.unit_or_topic}
                          onChange={(e) => handleUnitChange(idx, e.target.value)}
                        >
                          {config.selected_units?.map((u) => (
                            <option key={u} value={u}>
                              {u}
                            </option>
                          ))}
                        </select>
                      </label>

                      {/* Type Selector */}
                      <label className="q-mini-label">
                        Format:
                        <select
                          className="q-mini-select"
                          value={q.question_type}
                          onChange={(e) => handleTypeChange(idx, e.target.value)}
                        >
                          <option value="Short Answer">Short Answer</option>
                          <option value="Long Answer">Long Answer</option>
                          <option value="MCQ">MCQ</option>
                        </select>
                      </label>

                      {/* Marks Input */}
                      <label className="q-mini-label marks-label">
                        Marks:
                        <input
                          type="number"
                          className="q-marks-input"
                          min="1"
                          max="100"
                          value={q.marks}
                          onChange={(e) => handleMarksChange(idx, e.target.value)}
                        />
                      </label>

                      {/* Bloom's Tag if available */}
                      {q.blooms_level && (
                        <span className="blooms-tag">{q.blooms_level}</span>
                      )}

                      {/* Delete */}
                      <button
                        type="button"
                        className="delete-q-btn"
                        onClick={() => handleDeleteQuestion(idx)}
                        title="Delete Question"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>

                  {/* Question Textarea */}
                  <textarea
                    className="q-textarea"
                    rows={3}
                    value={q.question_text}
                    onChange={(e) => handleQuestionTextChange(idx, e.target.value)}
                    placeholder="Enter question text..."
                  />

                  {/* Single Question Relevance Footer */}
                  {rel && (
                    <div className="q-relevance-footer">
                      <span
                        className={`rel-badge ${
                          rel.status === "high"
                            ? "rel-high"
                            : rel.status === "review_required"
                            ? "rel-review"
                            : "rel-low"
                        }`}
                      >
                        Syllabus Relevance: {(rel.relevance_score * 100).toFixed(0)}% ({rel.status})
                      </span>
                      <span className="rel-explanation">{rel.explanation}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Actions Bar */}
        <div className="workflow-footer-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => goTo("paper_config")}
          >
            ← Back to Configuration
          </button>

          <div className="footer-right-actions">
            <span className="footer-marks-summary">
              Total Marks:{" "}
              <strong className={marksMatch ? "text-success" : "text-danger"}>
                {currentTotalMarks} / {targetTotalMarks}
              </strong>
            </span>

            <button
              type="button"
              className="primary-button hero-button"
              onClick={handleProceedToPreview}
            >
              Proceed to Final Preview & Export →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
