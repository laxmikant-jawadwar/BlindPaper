"""What the faculty preview and the admin review show about a paper: marks, relevance and checks."""

from app.services.paper_analysis import analyze
from tests.paper_helpers import MSE_GROUPS, SYLLABUS, config, group, sub


def question(slot_id: str, text: str, kind: str = "Descriptive", options=None, answer: str = "") -> dict:
    return {"sub_question_id": slot_id, "question_text": text, "question_type": kind, "options": options or [], "answer": answer}


OPTIONS = ["Moves between vertices", "Ignores constraints", "Only minimises", "Needs no variables"]

GOOD_QUESTIONS = [
    question("a1", "Which statement describes the simplex method for a linear programming problem?", "MCQ", OPTIONS, "A"),
    question("b1", "Explain the graphical method for solving a two variable linear programming problem.", "Descriptive"),
    question("c1", "Solve the linear programming problem by the simplex method: maximize Z = 3x1 + 5x2.", "Numerical"),
    question("a2", "Which statement is an assumption of the economic order quantity EOQ model for inventory?", "MCQ", OPTIONS, "C"),
    question("b2", "Discuss the inventory costs and the EOQ models used in inventory control.", "Descriptive"),
    question("c2", "Annual demand is 12000 units; compute the EOQ using the inventory costs given.", "Numerical"),
]


def paper(cfg=None, questions=None, **overrides) -> dict:
    cfg = cfg or config(MSE_GROUPS)
    data = {
        "groups": [g.model_dump() for g in cfg.groups],
        "selected_units": cfg.selected_units,
        "question_types": cfg.question_types,
        "questions": GOOD_QUESTIONS if questions is None else questions,
        "syllabus_snapshot": {"units": SYLLABUS["course_content"], "outcomes": SYLLABUS["course_outcomes"]},
    }
    return {**data, **overrides}


def check(report: dict, name: str) -> dict:
    return next(c for c in report["checks"] if c["name"] == name)


def test_marks_are_distributed_by_group_unit_and_course_outcome():
    report = analyze(paper())

    assert report["total_marks"] == 40
    assert [(g["group"], g["attempt"], g["of"], g["marks"]) for g in report["marks_by_group"]] == [(1, 2, 3, 20), (2, 2, 3, 20)]
    assert {u["unit_number"]: u["marks"] for u in report["marks_by_unit"]} == {1: 20, 2: 20}
    assert {c["co"]: c["marks"] for c in report["marks_by_co"]} == {"CO1": 20, "CO2": 20}


def test_unequal_marks_in_a_choose_any_group_make_the_total_ambiguous_so_it_is_flagged():
    groups = [group("g1", "Attempt any two", sub("a1", 5), sub("b1", 10), sub("c1", 10))]
    questions = [dict(q) for q in GOOD_QUESTIONS[:3]]

    report = analyze(paper(config(groups, selected_units=[1]), questions=questions))

    assert check(report, "marks")["status"] == "warn"
    assert "Q1" in check(report, "marks")["message"] and "5, 10, 10" in check(report, "marks")["message"]
    assert report["status"] == "warnings"


def test_unequal_marks_are_fine_when_every_question_in_the_group_must_be_answered():
    groups = [group("g1", "Attempt all", sub("a1", 5), sub("b1", 10), sub("c1", 10))]
    questions = [dict(q) for q in GOOD_QUESTIONS[:3]]

    report = analyze(paper(config(groups, selected_units=[1]), questions=questions))

    assert check(report, "marks")["status"] == "pass"
    assert report["total_marks"] == 25


def test_the_distributions_always_add_up_to_the_total_marks():
    groups = [group("g1", "Attempt any two", sub("a", 10, "CO1", 1), sub("b", 10, "CO2", 2), sub("c", 10, "CO3", 1))]

    report = analyze(paper(config(groups, selected_units=[1, 2]), questions=[]))

    assert report["total_marks"] == 20
    for key in ("marks_by_unit", "marks_by_co"):
        assert round(sum(item["marks"] for item in report[key]), 2) == 20


def test_a_complete_well_formed_paper_passes_every_check():
    report = analyze(paper())

    assert report["status"] == "pass"
    assert [c["status"] for c in report["checks"]] == ["pass"] * len(report["checks"])


def test_every_question_gets_a_relevance_score_against_its_unit():
    report = analyze(paper())

    scores = {r["sub_question_id"]: r for r in report["question_relevance"]}
    assert set(scores) == {"a1", "b1", "c1", "a2", "b2", "c2"}
    assert scores["b1"]["status"] == "high" and scores["b1"]["matched_terms"]
    assert scores["b1"]["label"] == "Q1b)"


def test_a_question_unrelated_to_its_unit_is_flagged_as_low_relevance():
    questions = [dict(q) for q in GOOD_QUESTIONS]
    questions[1]["question_text"] = "Describe the history of the Roman empire and its emperors."

    report = analyze(paper(questions=questions))

    assert check(report, "syllabus_relevance")["status"] == "warn"
    assert "Q1b)" in check(report, "syllabus_relevance")["message"]
    assert report["status"] == "warnings"


def test_a_symbolic_numerical_problem_cannot_be_judged_by_its_wording_so_it_is_not_flagged():
    questions = [dict(q) for q in GOOD_QUESTIONS]
    questions[2]["question_text"] = "Maximize Z = 3x1 + 5x2 subject to x1 <= 4, 2x2 <= 12 and 3x1 + 2x2 <= 18."

    report = analyze(paper(questions=questions))

    relevance = {r["sub_question_id"]: r for r in report["question_relevance"]}
    assert relevance["c1"]["status"] == "review_required"  # "needs a look", not "off-syllabus"
    assert check(report, "syllabus_relevance")["status"] == "pass"
    assert "Q1c)" in check(report, "syllabus_relevance")["message"]  # but the reviewer is told it was not judged
    assert report["status"] == "pass"


def test_a_missing_question_fails_the_structure_check():
    report = analyze(paper(questions=GOOD_QUESTIONS[:-1]))

    assert check(report, "structure")["status"] == "fail"
    assert "Q2c)" in check(report, "structure")["message"]
    assert report["status"] == "fail"


def test_an_mcq_needs_four_options_and_a_valid_answer():
    questions = [dict(q) for q in GOOD_QUESTIONS]
    questions[0]["options"] = OPTIONS[:3]
    questions[3]["answer"] = ""

    report = analyze(paper(questions=questions))

    assert check(report, "mcq_format")["status"] == "fail"
    assert "Q1a)" in check(report, "mcq_format")["message"] and "Q2a)" in check(report, "mcq_format")["message"]


def test_a_selected_unit_without_any_question_is_a_warning():
    groups = [group("g1", "Attempt all", sub("a", 5, "CO1", 1), sub("b", 5, "CO1", 1))]
    questions = [question("a", "Explain the graphical method for a linear programming problem."),
                 question("b", "Explain the simplex method for a linear programming problem.")]

    report = analyze(paper(config(groups, selected_units=[1, 2], question_types=["Descriptive"]), questions=questions))

    assert check(report, "unit_coverage")["status"] == "warn"
    assert "Unit 2" in check(report, "unit_coverage")["message"]


def test_a_selected_question_type_that_never_appears_is_a_warning():
    questions = [dict(q, question_type="Descriptive", options=[], answer="") for q in GOOD_QUESTIONS]

    report = analyze(paper(questions=questions))

    assert check(report, "question_types")["status"] == "warn"
    assert "MCQ" in check(report, "question_types")["message"]


def test_near_duplicate_questions_are_a_warning():
    questions = [dict(q) for q in GOOD_QUESTIONS]
    questions[2]["question_text"] = questions[1]["question_text"] + " Explain it."

    report = analyze(paper(questions=questions))

    assert check(report, "duplicates")["status"] == "warn"
    assert "Q1b)" in check(report, "duplicates")["message"] and "Q1c)" in check(report, "duplicates")["message"]


def test_markup_that_will_not_print_properly_is_a_warning():
    questions = [dict(q) for q in GOOD_QUESTIONS]
    questions[1]["question_text"] = "Explain the **graphical method** for a linear programming problem using $$x_1$$."

    report = analyze(paper(questions=questions))

    assert check(report, "formatting")["status"] == "warn"
