import { useState } from "react";
import { generateQuestionPaper } from "../api";

export function PaperConfig({
  goTo,
  uploadedSyllabus,
  onGenerationComplete,
}) {
  const defaultUnits = uploadedSyllabus?.units || [
    "Unit 1: Fundamentals",
    "Unit 2: Core Concepts",
    "Unit 3: Applications",
  ];

  const [subjectName, setSubjectName] = useState(
    uploadedSyllabus?.subject_name || "Data Structures"
  );
  const [selectedUnits, setSelectedUnits] = useState(defaultUnits);
  const [totalMarks, setTotalMarks] = useState(25);
  const [questionCount, setQuestionCount] = useState(5);
  const [questionTypes, setQuestionTypes] = useState([
    "Short Answer",
    "Long Answer",
  ]);
  const [difficulty, setDifficulty] = useState("medium");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const handleToggleUnit = (unitName) => {
    setSelectedUnits((prev) =>
      prev.includes(unitName)
        ? prev.filter((u) => u !== unitName)
        : [...prev, unitName]
    );
  };

  const handleToggleType = (type) => {
    setQuestionTypes((prev) => {
      const next = prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type];
      return next.length > 0 ? next : prev;
    });
  };

  const handleGenerate = async () => {
    setError(null);
    setSuccessMsg(null);

    if (!subjectName.trim()) {
      setError("Please provide a subject or course name.");
      return;
    }

    if (selectedUnits.length === 0) {
      setError("Please select at least one syllabus unit to include.");
      return;
    }

    if (questionTypes.length === 0) {
      setError("Please select at least one question type.");
      return;
    }

    if (Number(totalMarks) < Number(questionCount)) {
      setError(
        `Total marks (${totalMarks}) must be greater than or equal to question count (${questionCount}). Each question must carry at least 1 mark.`
      );
      return;
    }

    setLoading(true);

    try {
      const response = await generateQuestionPaper({
        subject_name: subjectName.trim(),
        syllabus_text:
          uploadedSyllabus?.extracted_text ||
          `Course: ${subjectName}\n${selectedUnits.join("\n")}`,
        selected_units: selectedUnits,
        total_marks: Number(totalMarks),
        question_count: Number(questionCount),
        question_types: questionTypes,
        difficulty: difficulty,
      });

      // Save to local recent papers list so dashboard displays it
      const newPaper = {
        id: "paper_" + Date.now(),
        subject_name: subjectName.trim(),
        filename: uploadedSyllabus?.filename || "syllabus.pdf",
        date: new Date().toISOString(),
        questions_count: Number(questionCount),
        total_marks: Number(totalMarks),
        status: "Approved",
        questions: response.questions,
      };

      const existing = JSON.parse(
        localStorage.getItem("blindpaper_recent_papers") || "[]"
      );
      localStorage.setItem(
        "blindpaper_recent_papers",
        JSON.stringify([newPaper, ...existing])
      );

      setSuccessMsg(
        `Question paper generated successfully for "${subjectName}" with ${response.questions.length} questions!`
      );

      if (onGenerationComplete) {
        onGenerationComplete(newPaper);
      }
    } catch (err) {
      setError(err.message || "Failed to generate question paper.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="clean-page-wrapper">
      <div className="clean-page-header">
        <button
          className="clean-back-btn"
          onClick={() => goTo("upload_pdf")}
          type="button"
        >
          ← Back to Upload
        </button>
        <span className="clean-step-badge">Step 2: Paper Configuration</span>
      </div>

      <div className="clean-card">
        <div className="clean-card-title-group">
          <h1>Paper Configuration</h1>
          <p>
            Provide your paper parameters to generate structured examination questions.
          </p>
        </div>

        {error && (
          <div className="clean-alert-error">
            <span>⚠️ {error}</span>
          </div>
        )}

        {successMsg && (
          <div className="clean-alert-success">
            <span>✓ {successMsg}</span>
            <button
              className="alert-link-btn"
              onClick={() => goTo("dashboard")}
              type="button"
            >
              Go to Dashboard →
            </button>
          </div>
        )}

        <div className="simple-config-form">
          {/* 1. Subject Name */}
          <div className="form-group">
            <label className="form-label" htmlFor="config-subject-name">
              Subject / Course Title:
            </label>
            <input
              id="config-subject-name"
              type="text"
              className="clean-input"
              value={subjectName}
              onChange={(e) => setSubjectName(e.target.value)}
              placeholder="e.g. Data Structures and Algorithms"
              required
            />
          </div>

          {/* 2. Units to Cover */}
          <div className="form-group">
            <div className="form-label-row">
              <label className="form-label">Syllabus Units to Include:</label>
              <span className="form-hint">
                ({selectedUnits.length} of {defaultUnits.length} selected)
              </span>
            </div>

            <div className="units-clean-checklist">
              {defaultUnits.map((unit, idx) => {
                const isChecked = selectedUnits.includes(unit);
                return (
                  <label
                    key={idx}
                    className={`unit-clean-item ${isChecked ? "active" : ""}`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleToggleUnit(unit)}
                    />
                    <span>{unit}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* 3. Marks & Question Count Row */}
          <div className="form-row-two">
            <div className="form-group">
              <label className="form-label" htmlFor="config-total-marks">
                Total Marks:
              </label>
              <input
                id="config-total-marks"
                type="number"
                className="clean-input"
                min="1"
                max="500"
                value={totalMarks}
                onChange={(e) =>
                  setTotalMarks(Math.max(1, parseInt(e.target.value, 10) || 1))
                }
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="config-question-count">
                Number of Questions:
              </label>
              <input
                id="config-question-count"
                type="number"
                className="clean-input"
                min="1"
                max="100"
                value={questionCount}
                onChange={(e) =>
                  setQuestionCount(
                    Math.max(1, parseInt(e.target.value, 10) || 1)
                  )
                }
                required
              />
            </div>
          </div>

          {/* 4. Difficulty & Question Formats Row */}
          <div className="form-row-two">
            <div className="form-group">
              <label className="form-label" htmlFor="config-difficulty">
                Difficulty Level:
              </label>
              <select
                id="config-difficulty"
                className="clean-select"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
                <option value="mixed">Mixed</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Question Types:</label>
              <div className="types-clean-checklist">
                {["Short Answer", "Long Answer", "MCQ"].map((type) => (
                  <label key={type} className="type-clean-item">
                    <input
                      type="checkbox"
                      checked={questionTypes.includes(type)}
                      onChange={() => handleToggleType(type)}
                    />
                    <span>{type}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Action Row */}
          <div className="clean-actions-row">
            <button
              className="primary-button"
              onClick={handleGenerate}
              disabled={loading}
              type="button"
            >
              {loading ? (
                <span className="spinner-btn-wrap">
                  <span className="spinner"></span>
                  Generating Questions...
                </span>
              ) : (
                "Generate Question Paper →"
              )}
            </button>

            <button
              className="secondary-button"
              onClick={() => goTo("dashboard")}
              disabled={loading}
              type="button"
            >
              Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
