"""API route modules."""
from app.api.routes.health import router as health_router
from app.api.routes.questions import router as questions_router
from app.api.routes.syllabus import router as syllabus_router
from app.api.routes.validation import router as validation_router

__all__ = ["health_router", "syllabus_router", "questions_router", "validation_router"]
