/**
 * API client service for BlindPaper frontend.
 * Communicates with the FastAPI backend using standard fetch.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Helper to process backend JSON response or throw formatted error.
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorMessage = `Server error (${response.status})`;
    try {
      const errorData = await response.json();
      if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail
          .map((err) => `${err.loc ? err.loc.join(".") + ": " : ""}${err.msg}`)
          .join("; ");
      }
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  return await response.json();
}

/**
 * Health check & database connection probe
 */
export async function getHealthStatus() {
  const response = await fetch(`${API_BASE}/api/health`);
  return handleResponse(response);
}

/**
 * Syllabus PDF upload and text extraction
 */
export async function uploadSyllabusFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/syllabus/upload`, {
    method: "POST",
    body: formData,
  });
  return handleResponse(response);
}

/**
 * Parse raw extracted syllabus text into structured units and Bloom's Taxonomy levels
 */
export async function structureSyllabusText({ extracted_text, subject_name, filename, page_count }) {
  const response = await fetch(`${API_BASE}/api/syllabus/structure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      extracted_text,
      subject_name: subject_name || undefined,
      filename: filename || "syllabus.pdf",
      page_count: page_count || 1,
    }),
  });
  return handleResponse(response);
}

/**
 * Save confirmed structured syllabus to MongoDB
 */
export async function saveSyllabusToDb(syllabusData) {
  const response = await fetch(`${API_BASE}/api/syllabus`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(syllabusData),
  });
  return handleResponse(response);
}

/**
 * List all saved syllabuses from MongoDB
 */
export async function listSavedSyllabi() {
  const response = await fetch(`${API_BASE}/api/syllabus`);
  return handleResponse(response);
}

/**
 * Retrieve single syllabus by ID from MongoDB
 */
export async function getSyllabusById(syllabusId) {
  const response = await fetch(`${API_BASE}/api/syllabus/${syllabusId}`);
  return handleResponse(response);
}

/**
 * Update syllabus in MongoDB
 */
export async function updateSyllabusInDb(syllabusId, updateData) {
  const response = await fetch(`${API_BASE}/api/syllabus/${syllabusId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updateData),
  });
  return handleResponse(response);
}

/**
 * Delete syllabus from MongoDB
 */
export async function deleteSyllabusFromDb(syllabusId) {
  const response = await fetch(`${API_BASE}/api/syllabus/${syllabusId}`, {
    method: "DELETE",
  });
  return handleResponse(response);
}

/**
 * Generate questions using examination configuration
 */
export async function generateQuestionPaper(config) {
  const response = await fetch(`${API_BASE}/api/questions/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  return handleResponse(response);
}

/**
 * Validate question paper for syllabus alignment, duplicates, and mark distributions
 */
export async function validateQuestionPaper(payload) {
  const response = await fetch(`${API_BASE}/api/questions/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Export approved question paper as downloadable PDF
 */
export async function exportQuestionPaperPdf(payload) {
  const response = await fetch(`${API_BASE}/api/questions/export-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorMsg = "Failed to export PDF";
    try {
      const err = await response.json();
      errorMsg = err.detail || errorMsg;
    } catch {
      errorMsg = response.statusText || errorMsg;
    }
    throw new Error(errorMsg);
  }

  // Extract filename from Content-Disposition header if available
  let filename = `${payload.subject_name.replace(/[^a-zA-Z0-9_-]/g, "_")}_Question_Paper.pdf`;
  const disposition = response.headers.get("Content-Disposition");
  if (disposition && disposition.includes("filename=")) {
    const match = disposition.match(/filename=["']?([^"';]+)["']?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  const blob = await response.blob();
  return { blob, filename };
}

export { API_BASE };
