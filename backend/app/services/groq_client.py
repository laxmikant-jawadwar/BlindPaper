"""A small client for Groq's OpenAI-compatible chat API that returns parsed JSON."""

import json
import math
from typing import Any, Dict, List, Optional, Tuple

import httpx


class GroqError(Exception):
    """A failed Groq call. `kind` says why: auth, rate_limit, server, network, invalid_output or bad_request."""

    def __init__(self, message: str, kind: str = "error", status_code: Optional[int] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code
        self.retry_after = retry_after


def _retry_after(response: httpx.Response) -> Optional[int]:
    raw = response.headers.get("retry-after")
    try:
        return math.ceil(float(raw)) if raw is not None else None
    except ValueError:
        return None


def _error_message(response: httpx.Response) -> str:
    try:
        return str(response.json()["error"]["message"])
    except Exception:
        return response.text[:200] or f"HTTP {response.status_code}"


class GroqClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float = 60.0,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._transport = transport  # lets tests replace the network

    def chat_json(
        self,
        model: str,
        messages: List[Dict[str, str]],
        json_schema: Optional[Dict[str, Any]] = None,
        reasoning_effort: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 4096,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Ask the model for a JSON answer. With json_schema the answer is forced to match it
        (strict mode); without, the model is only told to answer in JSON.
        Returns (parsed answer, token usage) or raises GroqError.
        """
        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
            "response_format": (
                {"type": "json_schema", "json_schema": {"name": "question_paper", "strict": True, "schema": json_schema}}
                if json_schema
                else {"type": "json_object"}
            ),
        }
        if reasoning_effort:
            body["reasoning_effort"] = reasoning_effort
            body["include_reasoning"] = False

        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as http:
                response = http.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=body,
                )
        except httpx.HTTPError as err:
            raise GroqError(f"could not reach Groq ({type(err).__name__})", kind="network") from err

        status = response.status_code
        if status in (401, 403):
            raise GroqError(_error_message(response), kind="auth", status_code=status)
        if status == 429:
            raise GroqError(_error_message(response), kind="rate_limit", status_code=status, retry_after=_retry_after(response))
        if status >= 500:
            raise GroqError(_error_message(response), kind="server", status_code=status)
        if status != 200:
            kind = "invalid_output" if "json_validate_failed" in response.text else "bad_request"
            raise GroqError(_error_message(response), kind=kind, status_code=status)

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
            return json.loads(content), data.get("usage", {})
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as err:
            raise GroqError("the model did not return valid JSON", kind="invalid_output", status_code=status) from err
