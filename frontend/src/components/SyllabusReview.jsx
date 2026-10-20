import { useState } from "react";
import { saveSyllabusToDb, updateSyllabusInDb } from "../api";

const BLOOMS_TAXONOMY_LEVELS = [
  "Remember",
  "Understand",
  "Apply",
  "Analyze",
  "Evaluate",
  "Create",
];

export function SyllabusReview({
  goTo,
  syllabusData,
  onSyllabusConfirmed,
}) {
  const [subjectName, setSubjectName] = useState(
    syllabusData?.subject_name || "Untitled Course"
  );
  const [units, setUnits] = useState(
    syllabusData?.structured_syllabus?.units || []
  );
  const [showRawText, setShowRawText] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Unit handlers
  const handleUnitNameChange = (unitIndex, newName) => {
    setUnits((prev) => {
      const copy = [...prev];
      copy[unitIndex] = { ...copy[unitIndex], unit_name: newName };
      return copy;
    });
  };

  const handleAddUnit = () => {
    const nextNum = units.length + 1;
    setUnits((prev) => [
      ...prev,
      {
        unit_name: `Unit ${nextNum}: New Unit Title`,
        topics: [
          {
            topic_name: "New Topic",
            subtopics: [],
            blooms_levels: ["Understand"],
            blooms_confidence: "needs_review",
          },
        ],
      },
    ]);
  };

  const handleRemoveUnit = (unitIndex) => {
    if (units.length <= 1) {
      alert("A syllabus must contain at least one unit.");
      return;
    }
    setUnits((prev) => prev.filter((_, idx) => idx !== unitIndex));
  };

  // Topic handlers
  const handleTopicNameChange = (unitIndex, topicIndex, newName) => {
    setUnits((prev) => {
      const copy = [...prev];
      const topicsCopy = [...copy[unitIndex].topics];
      topicsCopy[topicIndex] = {
        ...topicsCopy[topicIndex],
        topic_name: newName,
      };
      copy[unitIndex] = { ...copy[unitIndex], topics: topicsCopy };
      return copy;
    });
  };

  const handleToggleBloomsLevel = (unitIndex, topicIndex, level) => {
    setUnits((prev) => {
      const copy = [...prev];
      const topicsCopy = [...copy[unitIndex].topics];
      const currentLevels = topicsCopy[topicIndex].blooms_levels || [];
      const updatedLevels = currentLevels.includes(level)
        ? currentLevels.filter((l) => l !== level)
        : [...currentLevels, level];

      topicsCopy[topicIndex] = {
        ...topicsCopy[topicIndex],
        blooms_levels: updatedLevels.length > 0 ? updatedLevels : ["Understand"],
        blooms_confidence: "confirmed",
      };
      copy[unitIndex] = { ...copy[unitIndex], topics: topicsCopy };
      return copy;
    });
  };

  const handleAddTopic = (unitIndex) => {
    setUnits((prev) => {
      const copy = [...prev];
      const topicsCopy = [
        ...copy[unitIndex].topics,
        {
          topic_name: "New Topic",
          subtopics: [],
          blooms_levels: ["Understand"],
          blooms_confidence: "confirmed",
        },
      ];
      copy[unitIndex] = { ...copy[unitIndex], topics: topicsCopy };
      return copy;
    });
  };

  const handleRemoveTopic = (unitIndex, topicIndex) => {
    setUnits((prev) => {
      const copy = [...prev];
      if (copy[unitIndex].topics.length <= 1) {
        alert("Each unit must have at least one topic.");
        return prev;
      }
      const topicsCopy = copy[unitIndex].topics.filter((_, i) => i !== topicIndex);
      copy[unitIndex] = { ...copy[unitIndex], topics: topicsCopy };
      return copy;
    });
  };

  const handleConfirmAndSave = async () => {
    if (!subjectName.trim()) {
      setError("Please provide a valid Subject / Course Name.");
      return;
    }

    if (units.length === 0) {
      setError("At least one syllabus unit is required.");
      return;
    }

    setSaving(true);
    setError(null);

    const payload = {
      subject_name: subjectName.trim(),
      filename: syllabusData.filename || "syllabus.pdf",
      page_count: syllabusData.page_count || 1,
      extracted_text: syllabusData.extracted_text || "",
      structured_syllabus: {
        units: units,
      },
      processing_status: "reviewed",
    };

    try {
      let savedDoc;
      if (syllabusData.id) {
        // Updating existing syllabus document in MongoDB
        savedDoc = await updateSyllabusInDb(syllabusData.id, payload);
      } else {
        // Saving new syllabus document to MongoDB
        savedDoc = await saveSyllabusToDb(payload);
      }

      onSyllabusConfirmed(savedDoc);
      goTo("paper_config");
    } catch (err) {
      setError(`Failed to save syllabus to MongoDB: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="workflow-container">
      <div className="workflow-breadcrumbs">
        <button
          className="breadcrumb-btn"
          onClick={() => goTo(syllabusData.id ? "faculty_dashboard" : "upload_syllabus")}
          type="button"
        >
          ← Back
        </button>
        <span className="breadcrumb-step">Step 2 of 4: Syllabus Structuring & Review</span>
      </div>

      <div className="workflow-card">
        <div className="card-header">
          <div className="header-badge-row">
            <span className="card-eyebrow">FACULTY REVIEW</span>
            <span className="source-badge">
              📄 {syllabusData.filename} ({syllabusData.page_count} Pages)
            </span>
            {syllabusData.id && (
              <span className="id-badge" title={syllabusData.id}>
                MongoDB ID: {syllabusData.id.slice(0, 8)}...
              </span>
            )}
          </div>
          <h2>Review & Confirm Structured Syllabus</h2>
          <p className="card-desc">
            Verify the parsed units, topics, and Bloom's Taxonomy cognitive levels.
            Inferred levels are suggestions—you can adjust them to align with your
            assessment objectives before persisting to MongoDB.
          </p>
        </div>

        {error && (
          <div className="alert-box alert-error">
            <span className="alert-icon">⚠️</span>
            <div className="alert-body">
              <strong>Validation or Persistence Issue</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* Course Info Fields */}
        <div className="config-group">
          <label className="field-label" htmlFor="subject-name-input">
            Course / Subject Name:
            <input
              id="subject-name-input"
              type="text"
              className="text-input"
              value={subjectName}
              onChange={(e) => setSubjectName(e.target.value)}
              placeholder="e.g. Data Structures and Algorithms"
              required
            />
          </label>
        </div>

        {/* Collapsible Raw Text Preview */}
        <div className="raw-text-accordion">
          <button
            type="button"
            className="accordion-toggle"
            onClick={() => setShowRawText(!showRawText)}
          >
            <span>{showRawText ? "▼ Hide Extracted Raw Syllabus Text" : "▶ View Extracted Raw Syllabus Text"}</span>
            <span className="char-count">{syllabusData.extracted_text?.length || 0} characters</span>
          </button>
          {showRawText && (
            <pre className="raw-text-box">
              {syllabusData.extracted_text || "No raw text available."}
            </pre>
          )}
        </div>

        {/* Units & Topics List */}
        <div className="units-list-section">
          <div className="units-header-row">
            <h3>Units & Topics Breakdown ({units.length} Units)</h3>
            <button
              type="button"
              className="secondary-button"
              onClick={handleAddUnit}
            >
              + Add Unit
            </button>
          </div>

          <div className="units-stack">
            {units.map((unit, uIdx) => (
              <div key={uIdx} className="unit-card">
                <div className="unit-card-header">
                  <div className="unit-title-input-wrapper">
                    <span className="unit-num-badge">Unit {uIdx + 1}</span>
                    <input
                      type="text"
                      className="unit-name-input"
                      value={unit.unit_name}
                      onChange={(e) => handleUnitNameChange(uIdx, e.target.value)}
                      placeholder="Unit Name"
                    />
                  </div>
                  <button
                    type="button"
                    className="delete-unit-btn"
                    onClick={() => handleRemoveUnit(uIdx)}
                    title="Remove Unit"
                  >
                    🗑️
                  </button>
                </div>

                <div className="topics-sub-section">
                  <span className="topics-label">Topics & Bloom's Cognitive Levels:</span>
                  <div className="topics-stack">
                    {unit.topics.map((topic, tIdx) => (
                      <div key={tIdx} className="topic-card">
                        <div className="topic-header-row">
                          <input
                            type="text"
                            className="topic-name-input"
                            value={topic.topic_name}
                            onChange={(e) =>
                              handleTopicNameChange(uIdx, tIdx, e.target.value)
                            }
                            placeholder="Topic title"
                          />
                          <span
                            className={`confidence-pill ${
                              topic.blooms_confidence === "confirmed"
                                ? "pill-confirmed"
                                : topic.blooms_confidence === "inferred"
                                ? "pill-inferred"
                                : "pill-review"
                            }`}
                          >
                            {topic.blooms_confidence === "confirmed"
                              ? "✓ Confirmed"
                              : topic.blooms_confidence === "inferred"
                              ? "⚡ Inferred"
                              : "⚠️ Needs Review"}
                          </span>
                          <button
                            type="button"
                            className="delete-topic-btn"
                            onClick={() => handleRemoveTopic(uIdx, tIdx)}
                            title="Remove Topic"
                          >
                            ✕
                          </button>
                        </div>

                        {topic.subtopics && topic.subtopics.length > 0 && (
                          <div className="subtopics-chips">
                            {topic.subtopics.map((sub, sIdx) => (
                              <span key={sIdx} className="subtopic-chip">
                                • {sub}
                              </span>
                            ))}
                          </div>
                        )}

                        <div className="blooms-selector-row">
                          <span className="blooms-row-title">Bloom's Levels:</span>
                          <div className="blooms-pills-group">
                            {BLOOMS_TAXONOMY_LEVELS.map((level) => {
                              const isChecked = topic.blooms_levels?.includes(level);
                              return (
                                <button
                                  type="button"
                                  key={level}
                                  className={`blooms-chip-btn ${isChecked ? "active" : ""}`}
                                  onClick={() =>
                                    handleToggleBloomsLevel(uIdx, tIdx, level)
                                  }
                                >
                                  {isChecked ? "✓ " : ""}{level}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <button
                    type="button"
                    className="add-topic-btn"
                    onClick={() => handleAddTopic(uIdx)}
                  >
                    + Add Topic to Unit {uIdx + 1}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Row */}
        <div className="workflow-footer-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => goTo(syllabusData.id ? "faculty_dashboard" : "upload_syllabus")}
            disabled={saving}
          >
            ← Back
          </button>

          <button
            type="button"
            className="primary-button hero-button"
            onClick={handleConfirmAndSave}
            disabled={saving}
          >
            {saving
              ? "Saving to MongoDB..."
              : "Save to MongoDB & Configure Paper →"}
          </button>
        </div>
      </div>
    </div>
  );
}
