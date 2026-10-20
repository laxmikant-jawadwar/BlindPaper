"""A stand-in for Groq: canned answers in, every request recorded, no network and no quota used."""

import json

import httpx

from app.services.groq_client import GroqClient
from app.services.paper_generation_service import PaperGenerationService

MCQ_OPTIONS = [
    "A) It moves from one vertex of the feasible region to a better adjacent vertex.",
    "B) It always starts from the optimal solution.",
    "C) It only works for minimisation problems.",
    "D) It ignores the constraints.",
]


def valid_questions() -> list[dict]:
    """A good model answer for the default MSE template (a1 MCQ, b1 Descriptive, c1 Numerical, ...)."""
    def mcq(slot_id, text):
        return {"slot_id": slot_id, "question_text": text, "options": MCQ_OPTIONS, "answer": "A"}

    def plain(slot_id, text):
        return {"slot_id": slot_id, "question_text": text, "options": [], "answer": ""}

    return [
        mcq("a1", "Which statement best describes the simplex method?"),
        plain("b1", "Explain the graphical method for solving a two variable linear programming problem."),
        plain("c1", "Maximize Z = 3x1 + 5x2 subject to x1 <= 4, 2x2 <= 12 and 3x1 + 2x2 <= 18."),
        mcq("a2", "Which of the following is an assumption of the basic EOQ model?"),
        plain("b2", "Discuss the classification of inventory models with suitable examples."),
        plain("c2", "Annual demand is 12000 units, ordering cost is Rs 50 and holding cost is Rs 2 per unit. Find the EOQ."),
    ]


def completion(questions: list[dict]) -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": json.dumps({"questions": questions})}}], "usage": {"total_tokens": 1500}},
    )


def error_response(status: int, message: str = "boom", headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json={"error": {"message": message}}, headers=headers or {})


class FakeGroq:
    """Plays back canned responses in order and remembers every request it received."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests: list[dict] = []

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append({"headers": dict(request.headers), "body": json.loads(request.content)})
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def client_factory(self) -> GroqClient:
        return GroqClient("test-key", "https://api.groq.test/openai/v1", 5.0, transport=httpx.MockTransport(self._handle))

    def service(self) -> PaperGenerationService:
        return PaperGenerationService(client_factory=self.client_factory)
