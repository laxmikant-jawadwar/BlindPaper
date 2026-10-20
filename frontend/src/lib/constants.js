export const DEPARTMENTS = [
  "Computer Science",
  "Mechanical",
  "Civil",
  "Electrical",
  "Electronics",
  "Information Technology",
];

export const YEARS = ["First Year", "Second Year", "Third Year", "Final Year"];
export const SEMESTERS = Array.from({ length: 8 }, (_, i) => `Semester ${i + 1}`);

export const EXAM_TYPES = {
  MSE: { label: "MSE", description: "Mid Semester Examination", short: "Mid Semester" },
  ESE: { label: "ESE", description: "End Semester Examination", short: "End Semester" },
};

export const QUESTION_TYPES = [
  { value: "MCQ", label: "Multiple Choice Questions (MCQ)" },
  { value: "Descriptive", label: "Descriptive" },
  { value: "Numerical", label: "Numericals / Problem Solving" },
];

export const DIFFICULTIES = ["Easy", "Balanced", "Difficult"];

export const STATUS = {
  DRAFT: "Draft",
  PENDING: "Pending Approval",
  APPROVED: "Approved",
  REJECTED: "Rejected",
};
