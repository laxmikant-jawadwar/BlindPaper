import { useState } from "react";
import { generateQuestionPaper, validateQuestionPaper } from "../api";

const ALL_BLOOMS = [
  "Remember",
  "Understand",
  "Apply",
  "Analyze",
  "Evaluate",
  "Create",
];

const QUESTION_TYPES = ["Short Answer", "Long Answer", "MCQ"];

export function PaperConfig({
  goTo,
  syllabus,
  configState,
  onConfigChange,
  onGenerationComplete,
}) {
  const units = syllabus?.structured_syllabus?.units || [];
  const defaultUnitNames = units.map((u) => u.unit_name);

  // Form State, initialized from saved config or syllabus defaults
  const [subjectName, setSubjectName] = useState(
    configState?.subject_name || syllabus?.subject_name || "Data Structures"
  );
  const [selectedUnits, setSelectedUnits] = useState(
    configState?.selected_units || defaultUnitNames
  );
  const [totalMarks, setTotalMarks] = useState(configState?.total_marks || 25);
  const [questionCount, setQuestionCount] = useState(
    configState?.question_count || 5
  );
  const [questionTypes, setQuestionTypes] = useState(
    configState?.question_types || ["Short Answer", "Long Answer"]
  );
  const [difficulty, setDifficulty] = useState(
    configState?.difficulty || "medium"
  );
  const [selectedBlooms, setSelectedBlooms] = useState(
    configState?.blooms_levels || ["Understand", "Apply", "Analyze"]
  );

  // Optional exam header details
  const [collegeName, setCollegeName] = useState(
    configState?.college_name || "Department of Computer Science & Engineering"
  );
  const [examName, setExamName] = useState(
    configState?.exam_name || "Mid-Semester Examination 2026"
  );
  const [semester, setSemester] = useState(configState?.semester || "Semester V");
  const [paperCode, setPaperCode] = useState(configState?.paper_code || "CS-302");
  const [duration, setDuration] = useState(configState?.duration || "1.5 Hours");
  const [instructions, setInstructions] = useState(
    configState?.instructions || [
      "1. Answer all questions.",
      "2. Figures to the right indicate full marks.",
      "3. Use of non-programmable calculator is permitted.",
    ]
  );
  const [showMetadata, setShowMetadata] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Unit selection helpers
  const handleToggleUnit = (unitName) => {
    setSelectedUnits((prev) =>
      prev.includes(unitName)
        ? prev.filter((u) => u !== unitName)
        : [...prev, unitName]
    );
  };

  const handleSelectAllUnits = () => {
    setSelectedUnits(defaultUnitNames);
  };

  const handleDeselectAllUnits = () => {
    setSelectedUnits([]);
  };

  // Question type helpers
  const handleToggleType = (type) => {
    setQuestionTypes((prev) => {
      const next = prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type];
      return next.length > 0 ? next : prev;
    });
  };

  // Bloom's level helpers
  const handleToggleBloom = (level) => {
    setSelectedBlooms((prev) =>
      prev.includes(level)
        ? prev.filter((l) => l !== level)
        : [...prev, level]
    );
  };

  // Generate Handler
  const handleGenerate = async () => {
    setError(null);

    // Validation
    if (!subjectName.trim()) {
      setError("Please specify a course/subject name.");
      return;
    }

    if (selectedUnits.length === 0) {
      setError("Please select at least one syllabus unit.");
      return;
    }

    if (questionTypes.length === 0) {
      setError("Please select at least one question type.");
      return;
    }

    if (totalMarks < questionCount) {
      setError(
        `Total marks (${totalMarks}) cannot be less than question count (${questionCount}). Each question must carry at least 1 mark.`
      );
      return;
    }

    const currentConfig = {
      subject_name: subjectName.trim(),
      syllabus_id: syllabus.id || undefined,
      syllabus_text: syllabus.extracted_text || undefined,
      selected_units: selectedUnits,
      total_marks: Number(totalMarks),
      question_count: Number(questionCount),
      question_types: questionTypes,
      difficulty: difficulty,
      blooms_levels: selectedBlooms.length > 0 ? selectedBlooms : undefined,
      college_name: collegeName,
      exam_name: examName,
      semester: semester,
      paper_code: paperCode,
      duration: duration,
      instructions: instructions,
    };

    // Save configuration in state
    onConfigChange(currentConfig);

    setLoading(true);
    try {
      // 1. Call Question Generation API
      const genResponse = await generateQuestionPaper({
        subject_name: currentConfig.subject_name,
        syllabus_id: currentConfig.syllabus_id,
        syllabus_text: currentConfig.syllabus_text,
        selected_units: currentConfig.selected_units,
        total_marks: currentConfig.total_marks,
        question_count: currentConfig.question_count,
        question_types: currentConfig.question_types,
        difficulty: currentConfig.difficulty,
        blooms_levels: currentConfig.blooms_levels,
      });

      // 2. Automatically validate initial questions
      const valResponse = await validateQuestionPaper({
        subject_name: currentConfig.subject_name,
        syllabus_text: syllabus.extracted_text,
        selected_units: currentConfig.selected_units,
        questions: genResponse.questions,
        total_marks: currentConfig.total_marks,
        question_count: currentConfig.question_count,
      });

      onGenerationComplete({
        questions: genResponse.questions,
        generationMode: genResponse.generation_mode,
        generationMessage: genResponse.message,
        validationReport: valResponse,
      });

      goTo("question_review");
    } catch (err) {
      setError(err.message || "Failed to generate questions.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="workflow-container">
      <div className="workflow-breadcrumbs">
        <button
          className="breadcrumb-btn"
          onClick={() => goTo("syllabus_review")}
          type="button"
        >
          ← Back to Syllabus Structure
        </button>
        <span className="breadcrumb-step">Step 3 of 4: Examination Configuration</span>
      </div>

      <div className="workflow-card">
        <div className="card-header">
          <span className="card-eyebrow">BLUEPRINT & PARAMETERS</span>
          <h2>Configure Question Paper</h2>
          <p className="card-desc">
            Define syllabus coverage, marks allocation, question distribution,
            and cognitive difficulty before AI generates your examination questions.
          </p>
        </div>

        {error && (
          <div className="alert-box alert-error">
            <span className="alert-icon">⚠️</span>
            <div className="alert-body">
              <strong>Configuration Error</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        <div className="config-grid">
          {/* Left Column: Core Parameters */}
          <div className="config-column">
            <div className="config-field">
              <label className="field-label" htmlFor="paper-subject-input">
                Course / Subject Title:
                <input
                  id="paper-subject-input"
                  type="text"
                  className="text-input"
                  value={subjectName}
                  onChange={(e) => setSubjectName(e.target.value)}
                  placeholder="e.g. Data Structures & Algorithms"
                  required
                />
              </label>
            </div>

            <div className="config-row-two">
              <div className="config-field">
                <label className="field-label" htmlFor="total-marks-input">
                  Total Marks:
                  <input
                    id="total-marks-input"
                    type="number"
                    className="text-input"
                    min="1"
                    max="500"
                    value={totalMarks}
                    onChange={(e) => setTotalMarks(Math.max(1, Number(e.target.value)))}
                    required
                  />
                </label>
              </div>

              <div className="config-field">
                <label className="field-label" htmlFor="question-count-input">
                  Number of Questions:
                  <input
                    id="question-count-input"
                    type="number"
                    className="text-input"
                    min="1"
                    max="100"
                    value={questionCount}
                    onChange={(e) =>
                      setQuestionCount(Math.max(1, Number(e.target.value)))
                    }
                    required
                  />
                </label>
              </div>
            </div>

            <div className="config-field">
              <label className="field-label" htmlFor="difficulty-select">
                Overall Paper Difficulty:
                <select
                  id="difficulty-select"
                  className="select-input"
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                >
                  <option value="easy">Easy (Foundational & Definitions)</option>
                  <option value="medium">Medium (Standard College Exam)</option>
                  <option value="hard">Hard (Advanced & Critical Thinking)</option>
                  <option value="mixed">Mixed (Balanced Easy, Medium, Hard)</option>
                </select>
              </label>
            </div>

            <div className="config-field">
              <span className="field-label">Question Formats Desired:</span>
              <div className="checkboxes-row">
                {QUESTION_TYPES.map((type) => (
                  <label key={type} className="checkbox-label">
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

            <div className="config-field">
              <span className="field-label">Bloom's Taxonomy Target Focus:</span>
              <div className="blooms-pills-group">
                {ALL_BLOOMS.map((level) => {
                  const isChecked = selectedBlooms.includes(level);
                  return (
                    <button
                      type="button"
                      key={level}
                      className={`blooms-chip-btn ${isChecked ? "active" : ""}`}
                      onClick={() => handleToggleBloom(level)}
                    >
                      {isChecked ? "✓ " : ""}{level}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Units Selection */}
          <div className="config-column">
            <div className="unit-selection-card">
              <div className="unit-selection-header">
                <div>
                  <strong>Syllabus Units to Cover</strong>
                  <span className="selection-counter">
                    ({selectedUnits.length} of {units.length} selected)
                  </span>
                </div>
                <div className="bulk-selection-links">
                  <button
                    type="button"
                    className="text-link"
                    onClick={handleSelectAllUnits}
                  >
                    Select All
                  </button>
                  <span>•</span>
                  <button
                    type="button"
                    className="text-link"
                    onClick={handleDeselectAllUnits}
                  >
                    Clear All
                  </button>
                </div>
              </div>

              <div className="units-checkbox-list">
                {units.length === 0 ? (
                  <p className="no-units-msg">No units parsed from syllabus.</p>
                ) : (
                  units.map((unit, idx) => {
                    const isChecked = selectedUnits.includes(unit.unit_name);
                    return (
                      <label
                        key={idx}
                        className={`unit-checkbox-item ${isChecked ? "checked" : ""}`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handleToggleUnit(unit.unit_name)}
                        />
                        <div className="unit-checkbox-details">
                          <span className="unit-label-text">{unit.unit_name}</span>
                          <span className="unit-topics-count">
                            {unit.topics?.length || 0} topics
                          </span>
                        </div>
                      </label>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Optional Examination Header Metadata Accordion */}
        <div className="metadata-section">
          <button
            type="button"
            className="accordion-toggle"
            onClick={() => setShowMetadata(!showMetadata)}
          >
            <span>{showMetadata ? "▼ Examination PDF Header Details" : "▶ Examination PDF Header Details (Optional)"}</span>
            <span className="toggle-hint">College name, paper code, semester, instructions</span>
          </button>

          {showMetadata && (
            <div className="metadata-fields-grid">
              <div className="config-field">
                <label className="field-label" htmlFor="college-name-input">
                  College / University Name:
                  <input
                    id="college-name-input"
                    type="text"
                    className="text-input"
                    value={collegeName}
                    onChange={(e) => setCollegeName(e.target.value)}
                    placeholder="e.g. National Institute of Technology"
                  />
                </label>
              </div>

              <div className="config-field">
                <label className="field-label" htmlFor="exam-name-input">
                  Examination Title:
                  <input
                    id="exam-name-input"
                    type="text"
                    className="text-input"
                    value={examName}
                    onChange={(e) => setExamName(e.target.value)}
                    placeholder="e.g. End-Semester Examination"
                  />
                </label>
              </div>

              <div className="config-row-two">
                <div className="config-field">
                  <label className="field-label" htmlFor="semester-input">
                    Academic Year / Semester:
                    <input
                      id="semester-input"
                      type="text"
                      className="text-input"
                      value={semester}
                      onChange={(e) => setSemester(e.target.value)}
                      placeholder="e.g. Semester V"
                    />
                  </label>
                </div>

                <div className="config-field">
                  <label className="field-label" htmlFor="paper-code-input">
                    Paper Code:
                    <input
                      id="paper-code-input"
                      type="text"
                      className="text-input"
                      value={paperCode}
                      onChange={(e) => setPaperCode(e.target.value)}
                      placeholder="e.g. CS-401"
                    />
                  </label>
                </div>
              </div>

              <div className="config-field">
                <label className="field-label" htmlFor="duration-input">
                  Exam Duration:
                  <input
                    id="duration-input"
                    type="text"
                    className="text-input"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    placeholder="e.g. 2 Hours"
                  />
                </label>
              </div>

              <div className="config-field">
                <label className="field-label" htmlFor="instructions-input">
                  Candidate Instructions (one per line):
                  <textarea
                    id="instructions-input"
                    className="textarea-input"
                    rows={3}
                    value={instructions.join("\n")}
                    onChange={(e) =>
                      setInstructions(
                        e.target.value
                          .split("\n")
                          .filter((line) => line.trim().length > 0)
                      )
                    }
                  />
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Actions */}
        <div className="workflow-footer-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => goTo("syllabus_review")}
            disabled={loading}
          >
            ← Back to Syllabus Structure
          </button>

          <button
            type="button"
            className="primary-button hero-button"
            onClick={handleGenerate}
            disabled={loading}
          >
            {loading ? (
              <span className="button-spinner-row">
                <span className="spinner"></span>
                Generating Questions...
              </span>
            ) : (
              "Generate Question Paper →"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
