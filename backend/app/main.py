from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.export import router as export_router
from app.api.routes.health import router as health_router
from app.api.routes.questions import router as questions_router
from app.api.routes.syllabus import router as syllabus_router
from app.api.routes.validation import router as validation_router
from app.core.config import settings
from app.schemas.health import WelcomeResponse


def create_application() -> FastAPI:
    """
    Application factory that initializes and configures the FastAPI instance.
    """
    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description="Syllabus-centric AI question paper generation and validation backend.",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure Cross-Origin Resource Sharing (CORS) for frontend clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(health_router)
    app.include_router(syllabus_router)
    app.include_router(questions_router)
    app.include_router(validation_router)
    app.include_router(export_router)

    # Root welcome endpoint
    @app.get(
        "/",
        response_model=WelcomeResponse,
        tags=["General"],
        summary="Welcome endpoint",
        description="Returns a welcome message and basic API discovery link.",
    )
    def root() -> WelcomeResponse:
        """Return a friendly welcome message for the BlindPaper system."""
        return WelcomeResponse(
            message=f"Welcome to the {settings.app_name} API!",
            status="running",
            docs_url="/docs",
        )

    return app


app = create_application()
