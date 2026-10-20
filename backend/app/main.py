from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import ProblemsHTTPException, problems_handler
from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.papers import router as papers_router
from app.api.routes.syllabus import router as syllabus_router
from app.core.config import settings
from app.database.mongodb import close_database_connection
from app.schemas.health import WelcomeResponse
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown hooks.
    """
    logger.info(f"Starting {settings.app_name} API v{settings.app_version}...")
    try:
        auth_service.prepare()  # indexes + the admin account
    except Exception:
        # The API still starts without MongoDB; requests that need it report 503 instead
        logger.warning("Could not prepare MongoDB at startup (is it running?)", exc_info=True)
    yield
    logger.info("Shutting down BlindPaper API and releasing database connections...")
    close_database_connection()


def create_application() -> FastAPI:
    """
    Application factory that initializes and configures the FastAPI instance.
    """
    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description="Syllabus-centric AI question paper generation, review and approval backend.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure Cross-Origin Resource Sharing (CORS) for frontend clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # the browser may only read these response headers from another origin if they are listed
        expose_headers=["Content-Disposition", "Retry-After"],
    )

    # Register API routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(syllabus_router)
    app.include_router(papers_router)
    app.include_router(admin_router)
    app.add_exception_handler(ProblemsHTTPException, problems_handler)

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
