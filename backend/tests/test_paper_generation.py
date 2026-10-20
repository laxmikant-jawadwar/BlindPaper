"""Generating a paper with Groq: the prompt, checking the answer, falling back, and failing clearly."""

import httpx
import pytest

from app.core.config import settings
from app.services.paper_generation_service import (
    GenerationError,
    GenerationNotConfigured,
    GenerationRateLimited,
    PaperGenerationService,
)
from tests.groq_fake import MCQ_OPTIONS, FakeGroq, completion, error_response, valid_questions
from tests.paper_helpers import MSE_GROUPS, SYLLABUS, config, group, sub

def generate(fake: FakeGroq, cfg=None, syllabus=None):
    return fake.service().generate(cfg or config(MSE_GROUPS), syllabus or SYLLABUS)


def test_one_question_is_generated_for_every_slot_in_template_order():
    result = generate(FakeGroq(completion(valid_questions())))

    assert [q["sub_question_id"] for q in result.questions] == ["a1", "b1", "c1", "a2", "b2", "c2"]
    assert [q["question_type"] for q in result.questions] == ["MCQ", "Descriptive", "Numerical"] * 2
    assert result.model == settings.groq_model


def test_mcq_options_lose_their_letter_prefix_and_keep_the_answer_letter():
    first = generate(FakeGroq(completion(valid_questions()))).questions[0]

    assert first["options"][0] == "It moves from one vertex of the feasible region to a better adjacent vertex."
    assert len(first["options"]) == 4
    assert first["answer"] == "A"


def test_questions_that_are_not_multiple_choice_have_no_options_or_answer():
    second = generate(FakeGroq(completion(valid_questions()))).questions[1]

    assert second["options"] == [] and second["answer"] == ""


def test_the_request_asks_groq_for_strict_json_with_the_api_key():
    fake = FakeGroq(completion(valid_questions()))

    generate(fake)

    request = fake.requests[0]
    assert request["headers"]["authorization"] == "Bearer test-key"
    assert request["body"]["model"] == settings.groq_model
    assert request["body"]["response_format"]["type"] == "json_schema"
    assert request["body"]["response_format"]["json_schema"]["strict"] is True


def test_the_prompt_carries_the_template_the_selected_units_and_the_outcomes():
    groups = [group("g1", "Attempt any two", sub("a1", 2, "CO1", 1, "relate it to shadow prices"), sub("b1", 10, "CO2", 2))]
    fake = FakeGroq(completion(valid_questions()[:2]))

    generate(fake, config(groups, question_types=["MCQ", "Descriptive"], difficulty="Difficult"))

    prompt = fake.requests[0]["body"]["messages"][-1]["content"]
    for expected in (
        "Operations Research",
        "Difficult",
        "Simplex method",  # a topic of the selected unit 1
        "Concept of EOQ",  # a topic of the selected unit 2
        "Make use of Course knowledge to solve LPP",  # the description of CO2
        "relate it to shadow prices",  # the faculty's hint for the sub-question
        '"slot_id": "a1"',
    ):
        assert expected in prompt, expected
    assert "CPM and PERT" not in prompt  # Unit 3 was not selected


def test_a_missing_question_makes_the_fallback_model_try_again():
    incomplete = valid_questions()[:-1]
    fake = FakeGroq(completion(incomplete), completion(valid_questions()))

    result = generate(fake)

    assert [r["body"]["model"] for r in fake.requests] == [settings.groq_model, settings.groq_fallback_model]
    assert fake.requests[1]["body"]["response_format"] == {"type": "json_object"}
    assert result.model == settings.groq_fallback_model and len(result.questions) == 6


def test_an_mcq_whose_answer_is_not_one_of_its_options_is_rejected():
    bad = valid_questions()
    bad[0] = {**bad[0], "answer": "Z"}
    fake = FakeGroq(completion(bad), completion(valid_questions()))

    result = generate(fake)

    assert len(fake.requests) == 2 and result.model == settings.groq_fallback_model


def test_an_mcq_with_the_wrong_number_of_options_is_rejected():
    bad = valid_questions()
    bad[0] = {**bad[0], "options": MCQ_OPTIONS[:3]}
    fake = FakeGroq(completion(bad), completion(valid_questions()))

    generate(fake)

    assert len(fake.requests) == 2


def test_invalid_json_falls_back_to_the_other_model():
    garbled = httpx.Response(200, json={"choices": [{"message": {"content": "not json at all"}}], "usage": {}})
    fake = FakeGroq(garbled, completion(valid_questions()))

    result = generate(fake)

    assert len(fake.requests) == 2 and len(result.questions) == 6


def test_a_network_error_falls_back_to_the_other_model():
    fake = FakeGroq(httpx.ConnectError("no route"), completion(valid_questions()))

    assert len(generate(fake).questions) == 6
    assert len(fake.requests) == 2


def test_a_rate_limited_model_falls_back_to_the_other_one():
    fake = FakeGroq(error_response(429, "rate limit", {"retry-after": "9"}), completion(valid_questions()))

    result = generate(fake)

    assert result.model == settings.groq_fallback_model


def test_when_every_model_is_rate_limited_the_wait_time_is_reported():
    fake = FakeGroq(
        error_response(429, "rate limit", {"retry-after": "12"}),
        error_response(429, "rate limit", {"retry-after": "30"}),
    )

    with pytest.raises(GenerationRateLimited) as caught:
        generate(fake)

    assert caught.value.retry_after == 12  # the soonest either model is available again


def test_when_both_models_fail_the_error_explains_what_happened():
    fake = FakeGroq(error_response(500, "internal"), error_response(503, "overloaded"))

    with pytest.raises(GenerationError) as caught:
        generate(fake)

    assert "could not generate" in str(caught.value).lower()


def test_a_rejected_api_key_is_reported_and_not_retried():
    fake = FakeGroq(error_response(401, "Invalid API Key"))

    with pytest.raises(GenerationError) as caught:
        generate(fake)

    assert "api key" in str(caught.value).lower()
    assert len(fake.requests) == 1


def test_generation_needs_an_api_key(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)

    with pytest.raises(GenerationNotConfigured):
        PaperGenerationService().generate(config(MSE_GROUPS), SYLLABUS)


# ---- one question at a time ------------------------------------------------------------------------

def one_question(slot_id="b1", text="Describe how the graphical method finds the optimal corner point of a linear programming problem.", **extra):
    return {"slot_id": slot_id, "question_text": text, "options": extra.get("options", []), "answer": extra.get("answer", "")}


OLD_TEXTS = [q["question_text"] for q in valid_questions()]


def regenerate_one(fake, slot_id="b1", question_type="Descriptive", avoid=OLD_TEXTS):
    return fake.service().generate_question(config(MSE_GROUPS), SYLLABUS, slot_id, question_type, avoid)


def test_a_single_question_is_written_for_the_chosen_slot_only():
    result = regenerate_one(FakeGroq(completion([one_question()])))

    assert [q["sub_question_id"] for q in result.questions] == ["b1"]
    assert result.questions[0]["question_type"] == "Descriptive"
    assert result.questions[0]["question_text"].startswith("Describe how the graphical method")


def test_the_prompt_for_one_question_has_only_that_slot_and_the_questions_to_avoid():
    fake = FakeGroq(completion([one_question()]))

    regenerate_one(fake)

    prompt = fake.requests[0]["body"]["messages"][-1]["content"]
    assert '"slot_id": "b1"' in prompt
    for other in ("a1", "c1", "a2", "b2", "c2"):
        assert f'"slot_id": "{other}"' not in prompt
    assert "already_in_the_paper" in prompt
    assert OLD_TEXTS[1] in prompt  # the version being replaced
    assert "Simplex method" in prompt  # still grounded in the slot's unit topics


def test_a_regenerated_mcq_comes_with_options_and_a_correct_answer():
    mcq = one_question("a1", "Which statement about the dual of a linear programming problem is correct?", options=MCQ_OPTIONS, answer="A")

    result = regenerate_one(FakeGroq(completion([mcq])), slot_id="a1", question_type="MCQ")

    assert result.questions[0]["options"][0].startswith("It moves from one vertex") and result.questions[0]["answer"] == "A"


def test_a_regenerated_question_that_repeats_an_existing_one_is_rejected_and_the_fallback_tries_again():
    repeat = one_question(text=OLD_TEXTS[1].upper())  # same question, shouted
    fake = FakeGroq(completion([repeat]), completion([one_question()]))

    result = regenerate_one(fake)

    assert len(fake.requests) == 2 and result.model == settings.groq_fallback_model
    assert result.questions[0]["question_text"] != OLD_TEXTS[1]


# ---- option letters the model adds ------------------------------------------------------------------

def mcq_with(options):
    return [{**q, "options": options} if q["slot_id"] == "a1" else q for q in valid_questions()]


def test_option_letters_written_without_a_bracket_are_removed_when_all_four_have_them():
    options = ["A The dual of a maximisation problem is a minimisation problem.", "B The dual always has the same variables.",
               "C Duality does not apply to LPP.", "D The dual is unbounded."]

    first = generate(FakeGroq(completion(mcq_with(options)))).questions[0]

    assert first["options"] == [
        "The dual of a maximisation problem is a minimisation problem.", "The dual always has the same variables.",
        "Duality does not apply to LPP.", "The dual is unbounded.",
    ]


def test_an_option_that_merely_starts_with_the_word_a_is_left_alone():
    options = ["A linear function of the decision variables", "The simplex tableau", "An integer solution", "None of these"]

    first = generate(FakeGroq(completion(mcq_with(options)))).questions[0]

    assert first["options"] == options


def test_other_letter_styles_are_removed_too():
    options = ["(A) First option text", "(B) Second option text", "C. Third option text", "D: Fourth option text"]

    first = generate(FakeGroq(completion(mcq_with(options)))).questions[0]

    assert first["options"] == ["First option text", "Second option text", "Third option text", "Fourth option text"]
