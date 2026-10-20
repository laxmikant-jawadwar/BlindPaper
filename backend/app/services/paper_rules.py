"""
The rules behind a paper configuration. Pure functions: no database, no network.

- how many questions a group asks the student to attempt ("Attempt any two")
- the total marks of the paper
- which question type each sub-question gets
- whether the configuration is consistent with the uploaded syllabus
"""

import re
from typing import Any, Dict, List, Mapping, Sequence

from app.schemas.paper import PaperConfig, QuestionGroupSpec

CANONICAL_TYPES = ["MCQ", "Descriptive", "Numerical"]
DEFAULT_CO_CODES = [f"CO{i}" for i in range(1, 7)]
LOW_MARKS_FOR_MCQ = 2  # questions worth this much or less are multiple choice, when MCQ is selected

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}
_NUMBER_PATTERN = re.compile(r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\b")


def label_for(index: int) -> str:
    """0 -> 'a)', 1 -> 'b)' ..."""
    return f"{chr(ord('a') + index)})"


def attempt_count(instruction: str, available: int) -> int:
    """
    How many of a group's sub-questions the student answers.
    'Attempt any two' -> 2; 'Attempt all' or an instruction without a number -> all of them.
    """
    text = instruction.lower()
    if re.search(r"\ball\b", text):
        return available
    match = _NUMBER_PATTERN.search(text)
    if not match:
        return available
    token = match.group(1)
    return int(token) if token.isdigit() else NUMBER_WORDS[token]


def total_marks_for_groups(groups: Sequence[QuestionGroupSpec]) -> float:
    """
    Marks the student can score: for each group, the number attempted times the average marks
    of its sub-questions (which is simply their marks when they are all equal).
    """
    total = 0.0
    for group in groups:
        available = len(group.sub_questions)
        attempted = min(attempt_count(group.instruction, available), available)
        average = sum(sq.marks for sq in group.sub_questions) / available
        total += attempted * average
    return tidy_number(total)


def total_marks(config: PaperConfig) -> float:
    return total_marks_for_groups(config.groups)


def tidy_number(value: float) -> float:
    """Round to 2 decimals and show whole numbers as integers (40, not 40.0)."""
    value = round(value, 2)
    return int(value) if value.is_integer() else value


def assign_question_types(config: PaperConfig) -> Dict[str, str]:
    """
    Give every sub-question a question type, using each selected type in turn so all of them
    appear. Questions worth very few marks are multiple choice whenever MCQ is selected.
    """
    order = [t for t in CANONICAL_TYPES if t in config.question_types]
    assigned: Dict[str, str] = {}
    turn = 0
    for group in config.groups:
        for sub_question in group.sub_questions:
            # Every slot takes its turn in the rotation; a low-mark slot just overrides its turn with MCQ
            if sub_question.marks <= LOW_MARKS_FOR_MCQ and "MCQ" in order:
                assigned[sub_question.id] = "MCQ"
            else:
                assigned[sub_question.id] = order[turn % len(order)]
            turn += 1
    return assigned


def validate_config(config: PaperConfig, syllabus: Mapping[str, Any]) -> List[str]:
    """Everything wrong with this configuration, in words the faculty can act on. Empty if fine."""
    problems: List[str] = []

    syllabus_units = {unit["unit_number"] for unit in syllabus.get("course_content", [])}
    outcome_codes = [outcome["code"] for outcome in syllabus.get("course_outcomes", [])] or DEFAULT_CO_CODES

    for unit_number in config.selected_units:
        if unit_number not in syllabus_units:
            problems.append(f"Unit {unit_number} is not part of the uploaded syllabus.")

    for group_index, group in enumerate(config.groups, start=1):
        available = len(group.sub_questions)
        if attempt_count(group.instruction, available) > available:
            problems.append(
                f'Question {group_index}: "{group.instruction}" needs more questions than the group has '
                f"({available} sub-question{'s' if available != 1 else ''})."
            )
        for sub_index, sub_question in enumerate(group.sub_questions):
            where = f"Question {group_index}{label_for(sub_index)}"
            if sub_question.unit_number not in config.selected_units:
                problems.append(f"{where} uses Unit {sub_question.unit_number}, which is not selected.")
            if sub_question.co not in outcome_codes:
                problems.append(f"{where} uses {sub_question.co}, which is not a course outcome of this syllabus.")

    return problems
