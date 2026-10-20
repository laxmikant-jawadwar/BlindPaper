"""
What the faculty preview and the admin review show about a paper (application workflow, steps 5 and 10):
the marks distribution, how relevant each question is to the syllabus, and structure/format checks.
Works on the paper exactly as stored, so it can be recomputed whenever the paper is read or edited.
"""

import re
from typing import Any, Dict, List, Set

from app.schemas.paper import QuestionGroupSpec
from app.services import paper_rules
from app.services.text_similarity import compute_cosine_similarity, extract_informative_tokens

DUPLICATE_SIMILARITY = 0.70
RELEVANCE_HIGH = 0.40
RELEVANCE_REVIEW = 0.15
MIN_WORDS_TO_JUDGE = 4  # fewer real words than this (a symbolic numerical) cannot be judged by wording
_MARKUP = re.compile(r"\*\*|\$\$|\\\(|\\\[|\\frac|\\begin|^\s*#{1,6}\s|```", re.MULTILINE)


def _check(name: str, status: str, message: str) -> Dict[str, str]:
    return {"name": name, "status": status, "message": message}


def _labels(labels: List[str]) -> str:
    return ", ".join(labels)


def _distribution(slots: List[Dict[str, Any]], key: str, total: float) -> Dict[Any, float]:
    """
    Marks per unit (or CO). Shares are rounded to 2 decimals with the largest-remainder method,
    so the rounded figures add up to the paper's total exactly (no 20.01 on a 20-mark paper).
    """
    exact: Dict[Any, float] = {}
    for slot in slots:
        exact[slot[key]] = exact.get(slot[key], 0.0) + slot["effective_marks"]

    cents = {k: int(v * 100 + 1e-9) for k, v in exact.items()}
    leftover = round(total * 100) - sum(cents.values())
    by_remainder = sorted(exact, key=lambda k: exact[k] * 100 - cents[k], reverse=True)
    for k in by_remainder[: max(leftover, 0)]:
        cents[k] += 1
    return {k: paper_rules.tidy_number(c / 100) for k, c in cents.items()}


def _relevance(text: str, unit_tokens: Set[str]) -> Dict[str, Any]:
    tokens = set(extract_informative_tokens(text))
    matched = sorted(tokens & unit_tokens)
    score = round(len(matched) / len(tokens), 3) if tokens else 0.0
    words = [t for t in tokens if len(t) >= 3 and t.isalpha()]
    if score >= RELEVANCE_HIGH or len(matched) >= 3:
        status = "high"
    elif score >= RELEVANCE_REVIEW or matched or len(words) < MIN_WORDS_TO_JUDGE:
        status = "review_required"
    else:
        status = "low"
    return {"score": score, "status": status, "matched_terms": matched}


def analyze(paper: Dict[str, Any]) -> Dict[str, Any]:
    groups = [QuestionGroupSpec(**group) for group in paper["groups"]]
    questions = {q["sub_question_id"]: q for q in paper.get("questions", [])}
    snapshot = paper.get("syllabus_snapshot", {})
    units = {unit["unit_number"]: unit for unit in snapshot.get("units", [])}

    # ---- one record per slot, in template order -----------------------------------------
    slots: List[Dict[str, Any]] = []
    marks_by_group: List[Dict[str, Any]] = []
    for group_index, group in enumerate(groups, start=1):
        available = len(group.sub_questions)
        attempt = min(paper_rules.attempt_count(group.instruction, available), available)
        marks_by_group.append(
            {
                "group": group_index,
                "instruction": group.instruction,
                "attempt": attempt,
                "of": available,
                "marks": paper_rules.total_marks_for_groups([group]),
            }
        )
        for sub_index, sub_question in enumerate(group.sub_questions):
            slots.append(
                {
                    "id": sub_question.id,
                    "label": f"Q{group_index}{paper_rules.label_for(sub_index)}",
                    "unit_number": sub_question.unit_number,
                    "co": sub_question.co,
                    # what the slot contributes to the paper's total, given how many are attempted
                    "effective_marks": sub_question.marks * attempt / available,
                }
            )

    total = paper_rules.total_marks_for_groups(groups)
    marks_by_unit = [
        {
            "unit_number": number,
            "unit_name": units.get(number, {}).get("unit_name", f"Unit {number}"),
            "marks": marks,
        }
        for number, marks in sorted(_distribution(slots, "unit_number", total).items())
    ]
    marks_by_co = [{"co": co, "marks": marks} for co, marks in sorted(_distribution(slots, "co", total).items())]

    # ---- relevance of every question to its unit -----------------------------------------
    relevance: List[Dict[str, Any]] = []
    for slot in slots:
        question = questions.get(slot["id"])
        if not question:
            continue
        unit = units.get(slot["unit_number"], {})
        unit_tokens = set(extract_informative_tokens(" ".join([unit.get("unit_name", ""), *unit.get("topics", [])])))
        relevance.append({"sub_question_id": slot["id"], "label": slot["label"], **_relevance(question["question_text"], unit_tokens)})

    # ---- checks ---------------------------------------------------------------------------
    checks: List[Dict[str, str]] = []

    missing = [s["label"] for s in slots if s["id"] not in questions or not questions[s["id"]]["question_text"].strip()]
    checks.append(
        _check("structure", "fail", f"No question for {_labels(missing)}.")
        if missing
        else _check("structure", "pass", f"All {len(slots)} sub-questions have a question.")
    )

    over = [g for g in marks_by_group if paper_rules.attempt_count(g["instruction"], g["of"]) > g["of"]]
    checks.append(
        _check("attempt_instructions", "fail", "An attempt instruction asks for more questions than its group has.")
        if over
        else _check("attempt_instructions", "pass", "Every attempt instruction fits its group.")
    )

    # When students choose which questions to answer, every choice should carry the same marks
    uneven = [
        f"Q{number} ({', '.join(str(paper_rules.tidy_number(sq.marks)) for sq in group.sub_questions)})"
        for number, group in enumerate(groups, start=1)
        if len({sq.marks for sq in group.sub_questions}) > 1
        and paper_rules.attempt_count(group.instruction, len(group.sub_questions)) < len(group.sub_questions)
    ]
    if uneven:
        checks.append(
            _check(
                "marks",
                "warn",
                f"Students choose which questions to answer in {'; '.join(uneven)}, but their marks differ, "
                f"so the total of {total} is an average. Give the choices equal marks.",
            )
        )
    else:
        checks.append(_check("marks", "pass", f"Total marks: {total} across {len(groups)} question group{'s' if len(groups) != 1 else ''}."))

    selected_types = paper.get("question_types", [])
    used_types = {q["question_type"] for q in questions.values()}
    unused = [t for t in selected_types if t not in used_types]
    foreign = sorted(used_types - set(selected_types))
    if foreign:
        checks.append(_check("question_types", "warn", f"Questions use types that were not selected: {', '.join(foreign)}."))
    elif unused and len(slots) >= len(selected_types):
        checks.append(_check("question_types", "warn", f"{', '.join(unused)} was selected but no question uses it."))
    else:
        checks.append(_check("question_types", "pass", f"Question types used: {', '.join(sorted(used_types)) or 'none yet'}."))

    broken_mcq = []
    for slot in slots:
        question = questions.get(slot["id"])
        if question and question["question_type"] == "MCQ":
            options = [o for o in question.get("options", []) if str(o).strip()]
            if len(options) != 4 or question.get("answer") not in ("A", "B", "C", "D"):
                broken_mcq.append(slot["label"])
    checks.append(
        _check("mcq_format", "fail", f"These MCQs need 4 options and a correct answer: {_labels(broken_mcq)}.")
        if broken_mcq
        else _check("mcq_format", "pass", "Every MCQ has 4 options and a marked correct answer.")
    )

    used_units = {slot["unit_number"] for slot in slots}
    uncovered = [n for n in paper.get("selected_units", []) if n not in used_units]
    checks.append(
        _check("unit_coverage", "warn", f"No question covers {', '.join(f'Unit {n}' for n in uncovered)}.")
        if uncovered
        else _check("unit_coverage", "pass", "Every selected unit has at least one question.")
    )

    low = [r["label"] for r in relevance if r["status"] == "low"]
    unjudged = [r["label"] for r in relevance if r["status"] == "review_required" and not r["matched_terms"]]
    if low:
        checks.append(_check("syllabus_relevance", "warn", f"These questions look unrelated to their unit: {_labels(low)}."))
    elif unjudged:
        checks.append(
            _check(
                "syllabus_relevance", "pass",
                f"No question looks off-syllabus. {_labels(unjudged)} could not be judged by wording alone (mostly symbols); please read it.",
            )
        )
    else:
        checks.append(_check("syllabus_relevance", "pass", "Every question matches the topics of its unit."))

    labelled = [(slot["label"], questions[slot["id"]]["question_text"]) for slot in slots if slot["id"] in questions]
    similar = [
        (a, b)
        for i, (a, text_a) in enumerate(labelled)
        for b, text_b in labelled[i + 1:]
        if compute_cosine_similarity(text_a, text_b) >= DUPLICATE_SIMILARITY
    ]
    checks.append(
        _check("duplicates", "warn", "Near-duplicate questions: " + "; ".join(f"{a} and {b}" for a, b in similar) + ".")
        if similar
        else _check("duplicates", "pass", "No duplicate questions.")
    )

    markup = [label for label, text in labelled if _MARKUP.search(text)]
    checks.append(
        _check("formatting", "warn", f"These questions contain markup that will not print properly: {_labels(markup)}.")
        if markup
        else _check("formatting", "pass", "Questions are plain text and print cleanly.")
    )

    statuses = {c["status"] for c in checks}
    return {
        "total_marks": total,
        "marks_by_group": marks_by_group,
        "marks_by_unit": marks_by_unit,
        "marks_by_co": marks_by_co,
        "question_relevance": relevance,
        "checks": checks,
        "status": "fail" if "fail" in statuses else "warnings" if "warn" in statuses else "pass",
    }
