/**
 * The rules behind a paper configuration, mirroring backend/app/services/paper_rules.py so the
 * form can say what is wrong before anything is sent. The server still checks everything again.
 */

export const DEFAULT_CO_CODES = ["CO1", "CO2", "CO3", "CO4", "CO5", "CO6"];
export const MAX_MARKS = 100;

const NUMBER_WORDS = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10 };
const NUMBER_PATTERN = new RegExp(`\\b(\\d+|${Object.keys(NUMBER_WORDS).join("|")})\\b`);

/** "Attempt any two" -> 2; "Attempt all" or an instruction with no number -> every sub-question. */
export function attemptCount(instruction, available) {
  const text = (instruction || "").toLowerCase();
  if (/\ball\b/.test(text)) return available;
  const match = NUMBER_PATTERN.exec(text);
  if (!match) return available;
  return /^\d+$/.test(match[1]) ? Number(match[1]) : NUMBER_WORDS[match[1]];
}

/** Marks as the form holds them (a string while typing) -> a number, or null if it is not a positive number. */
export function parseMarks(value) {
  const text = String(value ?? "").trim();
  if (text === "") return null;
  const number = Number(text);
  return Number.isFinite(number) && number > 0 && number <= MAX_MARKS ? number : null;
}

/** What the student can score: for each group, the number attempted times the average marks of its sub-questions. */
export function totalMarks(groups) {
  let total = 0;
  for (const group of groups) {
    const available = group.subQuestions.length;
    if (!available) continue;
    const attempted = Math.min(attemptCount(group.instruction, available), available);
    const average = group.subQuestions.reduce((sum, sub) => sum + (parseMarks(sub.marks) ?? 0), 0) / available;
    total += attempted * average;
  }
  return Math.round(total * 100) / 100;
}

/**
 * Everything wrong with a configuration, for display beside the fields:
 *   fields   - course / year / semester / question types / units
 *   groups   - per group: an instruction or empty-group problem, and per sub-question: co, marks, unit
 *   messages - the same problems as plain sentences, for the summary box
 */
export function validateConfiguration({ courseName, courseCode, year, semester, questionTypes, selectedUnits, groups, coCodes }) {
  const fields = {};
  const groupErrors = {};
  const messages = [];
  const note = (message) => messages.push(message);

  if (!courseName.trim()) (fields.courseName = "Enter the course name."), note("Course name is empty.");
  if (!courseCode.trim()) (fields.courseCode = "Enter the course code."), note("Course code is empty.");
  if (!year) (fields.year = "Choose the year."), note("Choose the year.");
  if (!semester) (fields.semester = "Choose the semester."), note("Choose the semester.");
  if (!questionTypes.length) (fields.questionTypes = "Select at least one question type."), note("Select at least one question type.");
  if (!selectedUnits.length) (fields.units = "Select at least one unit."), note("Select at least one unit.");
  if (!groups.length) note("The template needs at least one question group.");

  groups.forEach((group, groupIndex) => {
    const where = `Question Group ${groupIndex + 1}`;
    const entry = { subs: {} };
    const available = group.subQuestions.length;

    if (!group.instruction.trim()) {
      entry.instruction = "Enter an attempt instruction, e.g. “Attempt any two”.";
      note(`${where}: the instruction is empty.`);
    } else if (!available) {
      entry.empty = "Add at least one sub-question.";
      note(`${where} has no sub-questions.`);
    } else if (attemptCount(group.instruction, available) > available) {
      entry.instruction = `“${group.instruction.trim()}” needs ${attemptCount(group.instruction, available)} questions, but this group has only ${available}.`;
      note(`${where}: ${entry.instruction}`);
    }
    if (!available && !entry.instruction && !entry.empty) entry.empty = "Add at least one sub-question.";

    group.subQuestions.forEach((sub, subIndex) => {
      const label = `${where}, ${String.fromCharCode(97 + subIndex)})`;
      const problems = {};
      if (!coCodes.includes(sub.co)) (problems.co = "Choose a course outcome."), note(`${label}: choose a course outcome.`);
      if (parseMarks(sub.marks) === null) {
        problems.marks = `Marks must be a number from 0.5 to ${MAX_MARKS}.`;
        note(`${label}: marks must be a positive number.`);
      }
      if (!selectedUnits.includes(sub.unitNumber)) (problems.unit = "Choose one of the selected units."), note(`${label}: choose one of the selected units.`);
      if (Object.keys(problems).length) entry.subs[sub.id] = problems;
    });

    if (entry.instruction || entry.empty || Object.keys(entry.subs).length) groupErrors[group.id] = entry;
  });

  return { fields, groups: groupErrors, messages, valid: messages.length === 0 };
}
