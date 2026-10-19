"""API route modules."""
from app.api.routes.health import router as health_router
from app.api.routes.syllabus import router as syllabus_router

__all__ = ["health_router", "syllabus_router"]
