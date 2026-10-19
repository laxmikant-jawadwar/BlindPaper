"""
Question generation service for BlindPaper.
Supports LLM provider generation (Gemini / OpenAI) with deterministic demo fallback.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.schemas.question import (
    QuestionGenerateRequest,
    QuestionGenerateResponse,
    QuestionItem,
)

logger = logging.getLogger(__name__)


class QuestionServiceError(Exception):
    """Base exception for question generation errors."""
    pass


class InvalidRequirementError(QuestionServiceError):
    """Raised when question count or marks distribution cannot be satisfied."""
    pass


class SyllabusMismatchError(QuestionServiceError):
    """Raised when requested topics/units are absent from the syllabus text."""
    pass


class LLMGenerationError(QuestionServiceError):
    """Raised when external LLM provider fails or produces invalid output."""
    pass


def distribute_marks(total_marks: int, question_count: int) -> List[int]:
    """
    Distribute total_marks across question_count questions as evenly as possible.
    Guarantees every question receives at least 1 mark and sum(marks) == total_marks.
    """
    if question_count <= 0:
        raise InvalidRequirementError("Question count must be greater than 0.")
    if total_marks < question_count:
        raise InvalidRequirementError(
            f"Cannot distribute {total_marks} marks across {question_count} questions. "
            "Every question requires at least 1 mark."
        )

    base = total_marks // question_count
    remainder = total_marks % question_count

    # Distribute the remainder across the first few questions
    marks = [base + 1 if i < remainder else base for i in range(question_count)]
    return marks


class DemoQuestionGenerator:
    """
    Deterministic question generator used when no external LLM API key is configured.
    Generates strictly syllabus-grounded questions and labels the output as 'demo'.
    """

    QUESTION_TEMPLATES = {
        "mcq": [
            "Which of the following best describes the core principle of {topic} in {subject}?",
            "In the context of {topic}, what is the primary purpose or operational role?",
            "Which condition or property is essential when implementing {topic}?",
        ],
        "short answer": [
            "Explain the basic concept and working mechanism of {topic}.",
            "Briefly discuss the significance and primary advantages of {topic}.",
            "Compare and contrast the primary approaches used in {topic}.",
        ],
        "long answer": [
            "Provide a detailed analysis of {topic} in {subject}, explaining its architecture and implementation.",
            "Discuss the theoretical foundations and practical applications of {topic} with suitable diagrams or illustrations.",
            "Critically evaluate the performance trade-offs and design challenges associated with {topic}.",
        ],
    }

    def generate(self, request: QuestionGenerateRequest) -> List[QuestionItem]:
        # Validate that at least one selected unit/topic is referenced in the syllabus text
        syllabus_lower = request.syllabus_text.lower()
        matched_units = [
            u for u in request.selected_units if u.lower() in syllabus_lower or any(word in syllabus_lower for word in u.lower().split() if len(word) > 3)
        ]

        if not matched_units:
            raise SyllabusMismatchError(
                "None of the selected units or topics were found in the supplied syllabus text. "
                "Questions cannot be generated without syllabus grounding."
            )

        marks_list = distribute_marks(request.total_marks, request.question_count)
        difficulty_cycle = ["easy", "medium", "hard"] if request.difficulty.lower() == "mixed" else [request.difficulty.lower()]

        questions: List[QuestionItem] = []
        for i in range(request.question_count):
            q_id = i + 1
            allocated_mark = marks_list[i]
            assigned_unit = matched_units[i % len(matched_units)]
            assigned_type = request.question_types[i % len(request.question_types)]
            assigned_diff = difficulty_cycle[i % len(difficulty_cycle)]

            # Select appropriate question text template
            type_key = assigned_type.lower()
            if "mcq" in type_key or "multiple" in type_key:
                templates = self.QUESTION_TEMPLATES["mcq"]
            elif "long" in type_key or "essay" in type_key or "detailed" in type_key:
                templates = self.QUESTION_TEMPLATES["long answer"]
            else:
                templates = self.QUESTION_TEMPLATES["short answer"]

            template = templates[i % len(templates)]
            q_text = template.format(topic=assigned_unit, subject=request.subject_name)

            questions.append(
                QuestionItem(
                    question_id=q_id,
                    question_text=q_text,
                    question_type=assigned_type,
                    unit_or_topic=assigned_unit,
                    marks=allocated_mark,
                    difficulty=assigned_diff,
                )
            )

        return questions


class LLMQuestionGenerator:
    """
    Question generator that invokes external LLM providers (Gemini / OpenAI).
    Requests structured JSON output and validates the response against syllabus requirements.
    """

    def __init__(self, api_key: str, provider: str = "gemini", model: Optional[str] = None) -> None:
        self.api_key = api_key
        self.provider = provider.lower()
        self.model = model or ("gemini-1.5-flash" if self.provider == "gemini" else "gpt-4o-mini")

    def _build_prompt(self, request: QuestionGenerateRequest) -> str:
        return f"""You are a college examination paper setter. Generate exactly {request.question_count} exam questions for the course "{request.subject_name}".

STRICT SYLLABUS GROUNDING RULES:
1. You MUST generate questions grounded ONLY in the following syllabus text.
2. DO NOT introduce any concepts, topics, or terminologies that are absent from this syllabus.
3. Target Units/Topics: {', '.join(request.selected_units)}
4. Allowed Question Types: {', '.join(request.question_types)}
5. Target Difficulty: {request.difficulty}
6. Total Marks: {request.total_marks} across all {request.question_count} questions combined.

SYLLABUS TEXT:
\"\"\"
{request.syllabus_text}
\"\"\"

RESPONSE REQUIREMENTS:
Return ONLY a valid JSON object with the following structure (no markdown formatting, no code blocks):
{{
  "questions": [
    {{
      "question_id": 1,
      "question_text": "Exact text of the question",
      "question_type": "Short Answer",
      "unit_or_topic": "Unit name or topic from syllabus",
      "marks": 5,
      "difficulty": "medium"
    }}
  ]
}}
Ensure the marks of all questions sum up to exactly {request.total_marks}.
"""

    def generate(self, request: QuestionGenerateRequest) -> List[QuestionItem]:
        prompt = self._build_prompt(request)

        try:
            if self.provider == "openai":
                raw_json_str = self._call_openai(prompt)
            else:
                raw_json_str = self._call_gemini(prompt)

            return self._parse_and_validate(raw_json_str, request)
        except QuestionServiceError:
            raise
        except Exception as err:
            logger.error("LLM Generation failed: %s", str(err))
            raise LLMGenerationError(f"LLM question generation failed: {str(err)}")

    def _call_gemini(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"},
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                raise LLMGenerationError(
                    f"Gemini API returned HTTP status {resp.status_code}: {resp.text}"
                )
            data = resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as err:
                raise LLMGenerationError("Gemini response missing content parts.") from err

    def _call_openai(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise LLMGenerationError(
                    f"OpenAI API returned HTTP status {resp.status_code}: {resp.text}"
                )
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as err:
                raise LLMGenerationError("OpenAI response missing message content.") from err

    def _parse_and_validate(self, raw_json_str: str, request: QuestionGenerateRequest) -> List[QuestionItem]:
        # Strip potential markdown code fence markers if model output them
        cleaned_str = raw_json_str.strip()
        if cleaned_str.startswith("```"):
            cleaned_str = re.sub(r"^```(?:json)?\n?", "", cleaned_str)
            cleaned_str = re.sub(r"\n?```$", "", cleaned_str).strip()

        try:
            parsed = json.loads(cleaned_str)
        except json.JSONDecodeError as err:
            raise LLMGenerationError(f"Model returned invalid JSON: {str(err)}")

        if not isinstance(parsed, dict) or "questions" not in parsed:
            raise LLMGenerationError("Model JSON output missing required 'questions' list.")

        raw_questions = parsed["questions"]
        if not isinstance(raw_questions, list):
            raise LLMGenerationError("'questions' property in model response is not a list.")

        if len(raw_questions) != request.question_count:
            raise InvalidRequirementError(
                f"LLM produced {len(raw_questions)} questions, but {request.question_count} were requested."
            )

        questions: List[QuestionItem] = []
        total_generated_marks = 0

        for i, item in enumerate(raw_questions):
            try:
                q = QuestionItem(
                    question_id=item.get("question_id", i + 1),
                    question_text=str(item["question_text"]).strip(),
                    question_type=str(item.get("question_type", request.question_types[0])).strip(),
                    unit_or_topic=str(item.get("unit_or_topic", request.selected_units[0])).strip(),
                    marks=int(item["marks"]),
                    difficulty=str(item.get("difficulty", request.difficulty)).strip(),
                )
            except Exception as e:
                raise LLMGenerationError(f"Malformed question item at index {i}: {str(e)}")

            total_generated_marks += q.marks
            questions.append(q)

        # Validate marks consistency
        if total_generated_marks != request.total_marks:
            # If the LLM was off by a small amount, adjust the distribution deterministically
            # to protect user from minor arithmetic hallucinations
            logger.warning(
                "LLM marks sum (%d) differed from requested (%d). Adjusting.",
                total_generated_marks,
                request.total_marks,
            )
            standardized_marks = distribute_marks(request.total_marks, request.question_count)
            for idx, q in enumerate(questions):
                q.marks = standardized_marks[idx]

        return questions


class QuestionService:
    """Orchestrates question paper generation across LLM and demo fallback providers."""

    def __init__(self) -> None:
        self.demo_generator = DemoQuestionGenerator()

    def generate_questions(self, request: QuestionGenerateRequest) -> QuestionGenerateResponse:
        """
        Generate questions based on examination requirements.
        Selects LLM provider if API key exists, otherwise falls back to deterministic demo generator.
        """
        api_key = settings.effective_api_key

        if api_key:
            # LLM generation mode
            generator = LLMQuestionGenerator(
                api_key=api_key,
                provider=settings.llm_provider,
                model=settings.llm_model,
            )
            questions = generator.generate(request)
            mode = "llm"
            message = f"Questions generated via {settings.llm_provider.capitalize()} LLM grounded in syllabus."
        else:
            # Deterministic demo fallback mode
            questions = self.demo_generator.generate(request)
            mode = "demo"
            message = (
                "Questions generated in demo mode (no LLM API key configured). "
                "Output is deterministically grounded in syllabus units."
            )

        calculated_marks = sum(q.marks for q in questions)

        return QuestionGenerateResponse(
            subject_name=request.subject_name,
            total_marks=calculated_marks,
            question_count=len(questions),
            generation_mode=mode,
            questions=questions,
            message=message,
        )


# Singleton question service instance
question_service = QuestionService()
