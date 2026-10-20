"""Sign up, sign in, sign out and the signed-in user's profile."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import bearer_scheme, get_current_user
from app.repositories.errors import DatabaseConnectionError
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserPublic,
)
from app.services.auth_service import (
    DuplicateEmailError,
    InvalidCredentialsError,
    auth_service,
    to_public_user,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Create a faculty account")
def register(request: RegisterRequest) -> AuthResponse:
    try:
        token, user = auth_service.register(request)
    except DuplicateEmailError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"MongoDB service is unavailable: {err}")
    return AuthResponse(token=token, user=to_public_user(user))


@router.post("/login", response_model=AuthResponse, summary="Sign in as faculty or admin")
def login(request: LoginRequest) -> AuthResponse:
    try:
        token, user = auth_service.login(request.email, request.password)
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"MongoDB service is unavailable: {err}")
    return AuthResponse(token=token, user=to_public_user(user))


@router.get("/me", response_model=UserPublic, summary="The signed-in user")
def me(user: Dict[str, Any] = Depends(get_current_user)) -> UserPublic:
    return UserPublic(**to_public_user(user))


@router.put("/me", response_model=UserPublic, summary="Update the signed-in user's profile")
def update_me(request: UpdateProfileRequest, user: Dict[str, Any] = Depends(get_current_user)) -> UserPublic:
    return UserPublic(**to_public_user(auth_service.update_profile(user["id"], request)))


@router.post("/logout", summary="Sign out (ends this session)")
def logout(
    _user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Dict[str, bool]:
    auth_service.logout(credentials.credentials)
    return {"success": True}
