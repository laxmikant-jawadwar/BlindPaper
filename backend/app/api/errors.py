"""HTTP errors that carry more than a message."""

from typing import List

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class ProblemsHTTPException(HTTPException):
    """A 422 whose body also lists each thing the user has to fix: {"detail": "...", "problems": [...]}."""

    def __init__(self, detail: str, problems: List[str]):
        super().__init__(status_code=422, detail=detail)
        self.problems = problems


async def problems_handler(_request: Request, exc: ProblemsHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "problems": exc.problems})
