"""The rules behind a paper configuration: attempt instructions, marks, question types, references."""

import pytest

from app.services import paper_rules
from tests.paper_helpers import MSE_GROUPS, SYLLABUS, config, group, sub


@pytest.mark.parametrize(
    "instruction, available, expected",
    [
        ("Attempt any two", 3, 2),
        ("attempt ANY THREE", 4, 3),
        ("Answer any 2 of the following", 3, 2),
        ("Attempt any two out of three", 3, 2),
        ("Attempt all", 3, 3),
        ("Solve the following", 3, 3),  # no number: everything is compulsory
        ("Attempt any one", 2, 1),
    ],
)
def test_attempt_count_is_read_from_the_instruction(instruction, available, expected):
    assert paper_rules.attempt_count(instruction, available) == expected


def test_total_marks_count_only_the_questions_the_student_attempts():
    # 2 groups, each "any two" of three 10-mark questions
    assert paper_rules.total_marks(config(MSE_GROUPS)) == 40


def test_total_marks_for_the_ese_template_with_a_four_question_group():
    groups = [
        group("g1", "Attempt any two", sub("a1"), sub("b1"), sub("c1")),
        group("g2", "Attempt any two", sub("a2"), sub("b2"), sub("c2")),
        group("g3", "Attempt any three", sub("a3", 5), sub("b3", 5), sub("c3", 5), sub("d3", 5)),
    ]

    assert paper_rules.total_marks(config(groups, exam_type="ESE")) == 20 + 20 + 15


def test_total_marks_with_unequal_marks_use_the_average_of_the_group():
    groups = [group("g1", "Attempt any two", sub("a", 4), sub("b", 6), sub("c", 8))]

    assert paper_rules.total_marks(config(groups)) == 12  # 2 x average(4, 6, 8)


def test_sub_question_labels_follow_the_alphabet():
    assert [paper_rules.label_for(i) for i in range(5)] == ["a)", "b)", "c)", "d)", "e)"]


def test_every_selected_question_type_is_used_in_turn():
    types = paper_rules.assign_question_types(config(MSE_GROUPS))

    assert [types[s] for s in ("a1", "b1", "c1", "a2", "b2", "c2")] == [
        "MCQ", "Descriptive", "Numerical", "MCQ", "Descriptive", "Numerical",
    ]


def test_low_mark_questions_are_multiple_choice_when_that_type_is_selected():
    groups = [group("g1", "Attempt all", sub("a", 2), sub("b", 10), sub("c", 10))]

    types = paper_rules.assign_question_types(config(groups, question_types=["MCQ", "Numerical"]))

    # a takes the MCQ turn anyway; b gets Numerical (not a second MCQ in a row); c comes round to MCQ again
    assert types == {"a": "MCQ", "b": "Numerical", "c": "MCQ"}


def test_a_low_mark_question_overrides_its_turn_without_skipping_the_rotation():
    groups = [group("g1", "Attempt all", sub("a", 10), sub("b", 2), sub("c", 10))]

    types = paper_rules.assign_question_types(config(groups, question_types=["MCQ", "Descriptive", "Numerical"]))

    # b's turn was Descriptive but it is worth 2 marks, so it becomes MCQ; c continues with Numerical
    assert types == {"a": "MCQ", "b": "MCQ", "c": "Numerical"}


def test_a_single_selected_type_applies_to_every_question():
    types = paper_rules.assign_question_types(config(MSE_GROUPS, question_types=["Descriptive"]))

    assert set(types.values()) == {"Descriptive"}


def test_a_valid_configuration_has_no_problems():
    assert paper_rules.validate_config(config(MSE_GROUPS), SYLLABUS) == []


def test_a_sub_question_may_not_use_an_unselected_unit():
    groups = [group("g1", "Attempt all", sub("a", unit=3))]

    problems = paper_rules.validate_config(config(groups), SYLLABUS)

    assert any("Unit 3" in p and "not selected" in p for p in problems)


def test_selected_units_must_exist_in_the_syllabus():
    problems = paper_rules.validate_config(config(MSE_GROUPS, selected_units=[1, 2, 9]), SYLLABUS)

    assert any("Unit 9" in p and "syllabus" in p for p in problems)


def test_a_co_must_exist_in_the_syllabus_outcomes():
    groups = [group("g1", "Attempt all", sub("a", co="CO6"))]

    problems = paper_rules.validate_config(config(groups), SYLLABUS)

    assert any("CO6" in p for p in problems)


def test_without_stored_outcomes_any_of_co1_to_co6_is_accepted():
    groups = [group("g1", "Attempt all", sub("a", co="CO6"))]

    assert paper_rules.validate_config(config(groups), {**SYLLABUS, "course_outcomes": []}) == []


def test_the_attempt_instruction_cannot_ask_for_more_than_there_are_questions():
    groups = [group("g1", "Attempt any three", sub("a"), sub("b"))]

    problems = paper_rules.validate_config(config(groups), SYLLABUS)

    assert any("Attempt any three" in p and "2 sub-question" in p for p in problems)
