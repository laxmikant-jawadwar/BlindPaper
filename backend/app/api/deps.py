"""Request dependencies: who is calling, and are they allowed to?"""

from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.constants import ROLE_ADMIN, ROLE_FACULTY
from app.services.auth_service import auth_service

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """The signed-in user, from the 'Authorization: Bearer <token>' header."""
    user = auth_service.user_for_token(credentials.credentials) if credentials else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not signed in, or your session has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_faculty(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user["role"] != ROLE_FACULTY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This area is for faculty members.")
    return user


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user["role"] != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This area is for the administrator.")
    return user
