"""Responses shared by the faculty and admin routes."""

import re
from typing import Any, Dict

from fastapi import Response

from app.services.paper_pdf_service import paper_pdf_service


def pdf_response(paper: Dict[str, Any]) -> Response:
    """The paper as a downloadable PDF."""
    safe_name = re.sub(r"[^\w\-]+", "_", f"{paper['course_code']}_{paper['exam_type']}").strip("_")
    return Response(
        content=paper_pdf_service.generate(paper),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="BlindPaper_{safe_name}.pdf"'},
    )
