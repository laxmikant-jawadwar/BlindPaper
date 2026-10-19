from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for the /api/health endpoint response."""

    status: str = Field(..., description="System health status (e.g., 'healthy')")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")


class WelcomeResponse(BaseModel):
    """Schema for the root / endpoint response."""

    message: str = Field(..., description="Welcome greeting message")
    status: str = Field(..., description="Application running status")
    docs_url: str = Field(..., description="Interactive API documentation URL")
