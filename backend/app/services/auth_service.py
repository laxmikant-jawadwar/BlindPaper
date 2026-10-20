"""Registration, login, sessions and profile updates."""

import logging
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple

from app.core.config import settings
from app.core.constants import ROLE_ADMIN, ROLE_FACULTY
from app.core.security import (
    DUMMY_HASH,
    hash_password,
    hash_token,
    new_session_token,
    verify_password,
)
from app.models.mongo import utcnow
from app.repositories.user_repository import DuplicateEmailError, user_repository
from app.schemas.auth import RegisterRequest, UpdateProfileRequest

logger = logging.getLogger(__name__)

__all__ = ["AuthService", "DuplicateEmailError", "InvalidCredentialsError", "auth_service", "to_public_user"]


class InvalidCredentialsError(Exception):
    """Raised for an unknown email or a wrong password (deliberately indistinguishable)."""


def to_public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """The user as the API returns it: no password hash, no internal fields."""
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "department": user.get("department"),
        "designation": user.get("designation"),
        "phone": user.get("phone"),
        "created_at": user.get("created_at", ""),
    }


class AuthService:
    def prepare(self) -> None:
        """Create database indexes and make sure the admin account exists."""
        user_repository.ensure_indexes()
        self.ensure_admin_user()

    def ensure_admin_user(self) -> None:
        """Create the admin from ADMIN_EMAIL / ADMIN_PASSWORD if it is not there yet."""
        if not settings.admin_email or not settings.admin_password:
            logger.warning("ADMIN_EMAIL / ADMIN_PASSWORD are not set; no admin account will be created.")
            return
        email = settings.admin_email.strip().lower()
        if user_repository.find_by_email(email):
            return
        user_repository.create(
            {
                "name": settings.admin_name,
                "email": email,
                "password_hash": hash_password(settings.admin_password),
                "role": ROLE_ADMIN,
                "department": None,
                "designation": "Exam Cell Authority",
                "phone": None,
            }
        )
        logger.info("Created admin account %s", email)

    def register(self, data: RegisterRequest) -> Tuple[str, Dict[str, Any]]:
        user = user_repository.create(
            {
                "name": data.name,
                "email": data.email,
                "password_hash": hash_password(data.password),
                "role": ROLE_FACULTY,
                "department": data.department,
                "designation": data.designation,
                "phone": data.phone,
            }
        )
        return self._start_session(user), user

    def login(self, email: str, password: str) -> Tuple[str, Dict[str, Any]]:
        user = user_repository.find_by_email(email)
        # Always run one hash check so an unknown email costs the same time as a wrong password
        if not verify_password(password, user["password_hash"] if user else DUMMY_HASH) or not user:
            raise InvalidCredentialsError()
        return self._start_session(user), user

    def logout(self, token: str) -> None:
        user_repository.delete_session(hash_token(token))

    def user_for_token(self, token: str) -> Optional[Dict[str, Any]]:
        session = user_repository.find_valid_session(hash_token(token))
        if not session:
            return None
        return user_repository.find_by_id(session["user_id"])

    def update_profile(self, user_id: str, data: UpdateProfileRequest) -> Dict[str, Any]:
        changes = data.model_dump(exclude_unset=True)
        for required in ("name", "department"):  # these can be changed but not cleared
            if changes.get(required) is None:
                changes.pop(required, None)
        return user_repository.update(user_id, changes)

    @staticmethod
    def _start_session(user: Dict[str, Any]) -> str:
        token = new_session_token()
        expires_at = utcnow() + timedelta(hours=settings.session_ttl_hours)
        user_repository.create_session(user["id"], hash_token(token), expires_at)
        return token


auth_service = AuthService()
