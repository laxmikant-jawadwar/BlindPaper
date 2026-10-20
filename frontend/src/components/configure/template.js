/**
 * The examination template as plain data and the pure functions that edit it.
 *   group:        { id, instruction, subQuestions: [subQuestion] }
 *   subQuestion:  { id, description, co, marks (a string while typing), unitNumber }
 * Every function returns a new array, so React state is never mutated.
 */

export function newId() {
  return globalThis.crypto?.randomUUID?.() ?? `id-${Math.random().toString(36).slice(2)}-${Date.now().toString(36)}`;
}

export function makeSubQuestion({ co, unitNumber, marks = "10", description = "" }) {
  return { id: newId(), description, co, marks: String(marks), unitNumber };
}

/** A group of `count` sub-questions that all start on the same outcome and unit. */
export function makeGroup({ instruction, count, co, unitNumber }) {
  return {
    id: newId(),
    instruction,
    subQuestions: Array.from({ length: count }, () => makeSubQuestion({ co, unitNumber })),
  };
}

const DEFAULT_SHAPES = {
  MSE: [
    { instruction: "Attempt any two", count: 3 },
    { instruction: "Attempt any two", count: 3 },
  ],
  ESE: [
    { instruction: "Attempt any two", count: 3 },
    { instruction: "Attempt any two", count: 3 },
    { instruction: "Attempt any three", count: 4 },
  ],
};

/** The standard MSE or ESE template. Group i starts on course outcome i and unit i, cycling if there are fewer. */
export function defaultTemplate(examType, coCodes, unitNumbers) {
  return DEFAULT_SHAPES[examType].map((shape, index) =>
    makeGroup({ ...shape, co: coCodes[index % coCodes.length], unitNumber: unitNumbers[index % unitNumbers.length] }),
  );
}

/** A new question group for "Add Question Group": three sub-questions, "Attempt any two". */
export function newGroup(groupCount, coCodes, unitNumbers) {
  return makeGroup({
    instruction: "Attempt any two",
    count: 3,
    co: coCodes[groupCount % coCodes.length],
    unitNumber: unitNumbers[groupCount % unitNumbers.length],
  });
}

const mapGroup = (groups, groupId, change) => groups.map((group) => (group.id === groupId ? change(group) : group));

export const updateGroup = (groups, groupId, patch) => mapGroup(groups, groupId, (group) => ({ ...group, ...patch }));

export const removeGroup = (groups, groupId) => groups.filter((group) => group.id !== groupId);

/** A new sub-question copies the outcome, unit and marks of the one above it. */
export function addSubQuestion(groups, groupId, fallback) {
  return mapGroup(groups, groupId, (group) => {
    const last = group.subQuestions[group.subQuestions.length - 1];
    const next = makeSubQuestion(last ? { co: last.co, unitNumber: last.unitNumber, marks: last.marks } : fallback);
    return { ...group, subQuestions: [...group.subQuestions, next] };
  });
}

export const removeSubQuestion = (groups, groupId, subId) =>
  mapGroup(groups, groupId, (group) => ({ ...group, subQuestions: group.subQuestions.filter((sub) => sub.id !== subId) }));

export const updateSubQuestion = (groups, groupId, subId, patch) =>
  mapGroup(groups, groupId, (group) => ({
    ...group,
    subQuestions: group.subQuestions.map((sub) => (sub.id === subId ? { ...sub, ...patch } : sub)),
  }));

/** Drag a sub-question onto another one in the same group: it takes that position. */
export function moveSubQuestion(groups, groupId, fromId, toId) {
  if (fromId === toId) return groups;
  return mapGroup(groups, groupId, (group) => {
    const items = [...group.subQuestions];
    const from = items.findIndex((sub) => sub.id === fromId);
    const to = items.findIndex((sub) => sub.id === toId);
    if (from < 0 || to < 0) return group;
    items.splice(to, 0, items.splice(from, 1)[0]);
    return { ...group, subQuestions: items };
  });
}

/** When a unit is deselected, every sub-question that used it moves to a unit that is still selected. */
export const reassignUnit = (groups, removedUnit, replacement) =>
  groups.map((group) => ({
    ...group,
    subQuestions: group.subQuestions.map((sub) => (sub.unitNumber === removedUnit ? { ...sub, unitNumber: replacement } : sub)),
  }));

/**
 * The units a fresh paper starts with. A mid-semester exam covers about the first half of the course
 * (syllabi say "first three modules"); an end-semester exam covers all of it.
 */
export function defaultUnitsFor(examType, unitNumbers) {
  if (examType === "ESE") return [...unitNumbers];
  return unitNumbers.slice(0, Math.max(1, Math.ceil(unitNumbers.length / 2)));
}

/** The unit numbers a template's sub-questions use. */
export const unitsUsedBy = (groups) => [...new Set(groups.flatMap((group) => group.subQuestions.map((sub) => sub.unitNumber)))];
