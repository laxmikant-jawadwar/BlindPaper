"""
Writes the questions of a paper with Groq (application workflow, step 4).

The faculty's template is a constraint, not an example: one question is written for every
sub-question slot, in the unit, for the course outcome and at the cognitive level of that slot.
The model's answer is checked before it is accepted; if it is unusable, a second model is tried.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, List, Optional

from app.core.config import settings
from app.schemas.paper import PaperConfig
from app.services import paper_rules
from app.services.groq_client import GroqClient, GroqError

logger = logging.getLogger(__name__)

EXAM_NAMES = {"MSE": "Mid Semester Examination (MSE)", "ESE": "End Semester Examination (ESE)"}

DIFFICULTY_GUIDE = {
    "Easy": "Mostly direct recall and understanding with simple, clean numbers.",
    "Balanced": "A sensible mix of understanding and application, like a typical university paper.",
    "Difficult": "Multi-step reasoning, analysis and evaluation; numericals need several steps and careful interpretation.",
}

SYSTEM_PROMPT = (
    "You are an experienced university examiner who writes clear, unambiguous exam questions. "
    "You only use topics that appear in the supplied syllabus units, and you write plain text "
    "(no LaTeX, no markdown): use simple notation such as x1, x2, <=, >=, Rs, and write Greek letters "
    "as words (lambda, mu, rho). Use a normal hyphen, never a non-breaking hyphen."
)

# Strict mode needs every property to be required, so non-MCQ questions carry an empty options list and answer
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slot_id": {"type": "string"},
                    "question_text": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}},
                    "answer": {"type": "string"},
                },
                "required": ["slot_id", "question_text", "options", "answer"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}

_OPTION_PREFIX = re.compile(r"^\(?[A-D][\).:]\s+")
_BARE_LETTERS = [re.compile(rf"^{letter}\s+") for letter in "ABCD"]
_ANSWER_LETTER = re.compile(r"^\s*(?:option\s*)?\(?([A-Da-d])\b")


class GenerationError(Exception):
    """The paper could not be generated; the message is safe to show the faculty."""


class GenerationNotConfigured(GenerationError):
    """No Groq API key is configured."""


class GenerationRateLimited(GenerationError):
    def __init__(self, retry_after: Optional[int]):
        wait = f" Try again in about {retry_after} seconds." if retry_after else " Try again in a minute."
        super().__init__("The AI service is busy (rate limit reached)." + wait)
        self.retry_after = retry_after


class InvalidModelOutput(Exception):
    """The model answered, but not with a usable paper."""


@dataclass
class GenerationResult:
    questions: List[Dict[str, Any]]
    model: str
    usage: Dict[str, Any] = field(default_factory=dict)


def build_slots(config: PaperConfig, syllabus: Dict[str, Any]) -> List[Dict[str, Any]]:
    """One entry per sub-question slot, with everything the model needs to write that question."""
    units = {unit["unit_number"]: unit for unit in syllabus.get("course_content", [])}
    outcomes = {outcome["code"]: outcome for outcome in syllabus.get("course_outcomes", [])}
    types = paper_rules.assign_question_types(config)

    slots: List[Dict[str, Any]] = []
    for group_index, group in enumerate(config.groups, start=1):
        for sub_index, sub_question in enumerate(group.sub_questions):
            unit = units[sub_question.unit_number]
            outcome = outcomes.get(sub_question.co)
            slot: Dict[str, Any] = {
                "slot_id": sub_question.id,
                "question_number": f"Q{group_index}{paper_rules.label_for(sub_index)}",
                "marks": sub_question.marks,
                "question_type": types[sub_question.id],
                "unit": f"Unit {unit['unit_number']}: {unit['unit_name']}",
                "unit_topics": unit.get("topics", []),
                "course_outcome": f"{outcome['code']}: {outcome['description']}" if outcome else sub_question.co,
            }
            if outcome and outcome.get("blooms_descriptor"):
                slot["cognitive_level"] = f"{outcome['blooms_descriptor']} (Bloom level {outcome.get('blooms_level')})"
            if sub_question.description:
                slot["faculty_hint"] = sub_question.description
            slots.append(slot)
    return slots


def build_messages(config: PaperConfig, slots: List[Dict[str, Any]], avoid: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    The prompt for a whole paper or, with `avoid` (the questions already in the paper), for one replacement
    question that must differ from all of them.
    """
    specification = {
        "course": f"{config.course_name} ({config.course_code})",
        "exam": EXAM_NAMES[config.exam_type],
        "year_and_semester": f"{config.year}, {config.semester}",
        "overall_difficulty": f"{config.difficulty}: {DIFFICULTY_GUIDE[config.difficulty]}",
        "rules": [
            "Write exactly one question for every slot, using the slot_id given, in the same order.",
            "Stay strictly inside the slot's unit_topics. Never use topics from other units.",
            "Match the slot's cognitive_level and the depth expected for its marks (2 marks = short, 10 marks = detailed).",
            "If a slot has a faculty_hint, follow it.",
            "MCQ: give exactly 4 plausible options in 'options' and the correct option letter (A, B, C or D) in 'answer'. "
            "Check that exactly one option is correct.",
            "Numerical: give concrete numbers and a fully specified problem that can be solved by hand; "
            "the numbers must lead to a sensible answer.",
            "Descriptive: ask for explanation, derivation, comparison or discussion suited to the marks.",
            "For every question that is not an MCQ, return an empty options list and an empty answer.",
            "Do not mention marks, CO or unit inside question_text.",
        ],
        "slots": slots,
    }
    task = "Write the paper for this specification and answer with JSON only.\n"
    if avoid:
        specification["already_in_the_paper"] = [text[:400] for text in avoid]
        specification["rules"].append(
            "These questions are already in the paper (including the one being replaced). Write a clearly different new "
            "question for the slot: a new scenario, different numbers or a different angle. Do not repeat or lightly reword any of them."
        )
        task = "Write one replacement question for the slot in this specification and answer with JSON only.\n"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task + json.dumps(specification, ensure_ascii=False)},
    ]


def _clean_options(options: Any) -> List[str]:
    """Remove the letters models like to put in front of MCQ options ('A)', '(B)', 'C.', 'D:' or a bare 'A ')."""
    if not isinstance(options, list):
        return []
    raw = [str(option).strip() for option in options]
    # A bare letter ("A The dual of...") is also how a real option can begin ("A linear function..."), so it is only
    # treated as a label when all four options carry the letters A, B, C, D in order.
    if len(raw) == 4 and all(pattern.match(text) for pattern, text in zip(_BARE_LETTERS, raw)):
        return [pattern.sub("", text, count=1).strip() for pattern, text in zip(_BARE_LETTERS, raw)]
    return [_OPTION_PREFIX.sub("", text).strip() for text in raw]


def _same_question(text: str) -> str:
    """A question's wording reduced to lower-case words, so 'Explain X.' and 'EXPLAIN  x' count as the same."""
    return " ".join(re.sub(r"\W+", " ", text.lower()).split())


def _parse_questions(data: Any, slots: List[Dict[str, Any]], forbidden: FrozenSet[str] = frozenset()) -> List[Dict[str, Any]]:
    items = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise InvalidModelOutput("the answer had no list of questions")

    by_slot = {str(item.get("slot_id")): item for item in items if isinstance(item, dict)}
    missing = [slot["slot_id"] for slot in slots if slot["slot_id"] not in by_slot]
    if missing:
        raise InvalidModelOutput(f"no question was written for: {', '.join(missing)}")

    questions: List[Dict[str, Any]] = []
    for slot in slots:
        item = by_slot[slot["slot_id"]]
        text = str(item.get("question_text", "")).strip()
        if len(text) < 10:
            raise InvalidModelOutput(f"the question for {slot['question_number']} is empty or too short")
        if _same_question(text) in forbidden:
            raise InvalidModelOutput(f"the question for {slot['question_number']} repeats one that is already in the paper")

        options: List[str] = []
        answer = ""
        if slot["question_type"] == "MCQ":
            options = _clean_options(item.get("options"))
            if len(options) != 4 or not all(options):
                raise InvalidModelOutput(f"the MCQ for {slot['question_number']} does not have 4 options")
            match = _ANSWER_LETTER.match(str(item.get("answer", "")))
            if not match:
                raise InvalidModelOutput(f"the MCQ for {slot['question_number']} has no correct option")
            answer = match.group(1).upper()

        questions.append(
            {
                "sub_question_id": slot["slot_id"],
                "question_text": text,
                "question_type": slot["question_type"],
                "options": options,
                "answer": answer,
            }
        )
    return questions


class PaperGenerationService:
    def __init__(self, client_factory: Optional[Callable[[], GroqClient]] = None) -> None:
        self._client_factory = client_factory

    def _client(self) -> GroqClient:
        if self._client_factory:
            return self._client_factory()
        if not settings.groq_api_key:
            raise GenerationNotConfigured("Question generation is not configured: set GROQ_API_KEY in backend/.env.")
        return GroqClient(settings.groq_api_key, settings.groq_base_url, settings.groq_timeout_seconds)

    def generate(self, config: PaperConfig, syllabus: Dict[str, Any]) -> GenerationResult:
        """Write the whole paper: one question for every slot of the template."""
        slots = build_slots(config, syllabus)
        return self._run(slots, build_messages(config, slots), lambda data: _parse_questions(data, slots))

    def generate_question(
        self, config: PaperConfig, syllabus: Dict[str, Any], slot_id: str, question_type: str, avoid: List[str]
    ) -> GenerationResult:
        """
        Write one replacement question for a single slot, keeping its type. `avoid` is every question
        currently in the paper (including the one being replaced); the answer must not repeat any of them.
        """
        slot = {**next(s for s in build_slots(config, syllabus) if s["slot_id"] == slot_id), "question_type": question_type}
        forbidden = frozenset(_same_question(text) for text in avoid)
        return self._run([slot], build_messages(config, [slot], avoid), lambda data: _parse_questions(data, [slot], forbidden))

    def _run(self, slots: List[Dict[str, Any]], messages: List[Dict[str, str]], parse: Callable[[Any], List[Dict[str, Any]]]) -> GenerationResult:
        """Ask the main model; if it is busy or its answer is unusable, ask the fallback model."""
        client = self._client()
        max_tokens = min(6000, 900 + 350 * len(slots))

        models = [settings.groq_model]
        if settings.groq_fallback_model and settings.groq_fallback_model != settings.groq_model:
            models.append(settings.groq_fallback_model)

        failures: List[GroqError] = []
        for index, model in enumerate(models):
            try:
                data, usage = client.chat_json(
                    model,
                    messages,
                    json_schema=RESPONSE_SCHEMA if index == 0 else None,
                    reasoning_effort="medium" if model.startswith("openai/gpt-oss") else None,
                    max_tokens=max_tokens,
                )
                return GenerationResult(parse(data), model, usage)
            except GroqError as err:
                if err.kind == "auth":
                    raise GenerationError("Groq rejected the API key. Check GROQ_API_KEY in backend/.env.") from err
                logger.warning("Groq model %s failed (%s): %s", model, err.kind, err)
                failures.append(err)
            except InvalidModelOutput as err:
                logger.warning("Groq model %s gave an unusable paper: %s", model, err)
                failures.append(GroqError(str(err), kind="invalid_output"))

        if all(failure.kind == "rate_limit" for failure in failures):
            waits = [f.retry_after for f in failures if f.retry_after is not None]
            raise GenerationRateLimited(min(waits) if waits else None)
        reasons = "; ".join(f"{model}: {failure}" for model, failure in zip(models, failures))
        raise GenerationError(f"Could not generate the paper ({reasons}). Please try again.")


paper_generation_service = PaperGenerationService()
