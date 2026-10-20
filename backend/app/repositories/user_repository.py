"""MongoDB access for user accounts and login sessions."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo.errors import DuplicateKeyError, PyMongoError

from app.database.mongodb import get_sessions_collection, get_users_collection
from app.models.mongo import get_utc_now_iso, parse_object_id, serialize_mongo_doc, utcnow
from app.repositories.errors import DatabaseConnectionError

logger = logging.getLogger(__name__)


class DuplicateEmailError(Exception):
    """Raised when an account with this email already exists."""


class UserRepository:
    def __init__(self, users_provider=get_users_collection, sessions_provider=get_sessions_collection):
        self._users = users_provider
        self._sessions = sessions_provider

    # ---- users -------------------------------------------------------
    def ensure_indexes(self) -> None:
        self._users().create_index("email", unique=True)
        self._sessions().create_index("token_hash", unique=True)
        # MongoDB removes expired sessions on its own
        self._sessions().create_index("expires_at", expireAfterSeconds=0)

    def create(self, user: Dict[str, Any]) -> Dict[str, Any]:
        now = get_utc_now_iso()
        doc = {**user, "created_at": now, "updated_at": now}
        try:
            doc["_id"] = self._users().insert_one(doc).inserted_id
        except DuplicateKeyError as err:
            raise DuplicateEmailError(user.get("email", "")) from err
        except PyMongoError as err:
            raise DatabaseConnectionError(f"Database insert error: {err}") from err
        return serialize_mongo_doc(doc)

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        doc = self._users().find_one({"email": email})
        return serialize_mongo_doc(doc) if doc else None

    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        oid = parse_object_id(user_id)
        if oid is None:
            return None
        doc = self._users().find_one({"_id": oid})
        return serialize_mongo_doc(doc) if doc else None

    def update(self, user_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        oid = parse_object_id(user_id)
        if oid is None:
            return None
        self._users().update_one({"_id": oid}, {"$set": {**fields, "updated_at": get_utc_now_iso()}})
        return self.find_by_id(user_id)

    def list_by_role(self, role: str) -> List[Dict[str, Any]]:
        return [serialize_mongo_doc(d) for d in self._users().find({"role": role}).sort("created_at", 1)]

    def count_by_role(self, role: str) -> int:
        return self._users().count_documents({"role": role})

    # ---- sessions ----------------------------------------------------
    def create_session(self, user_id: str, token_hash: str, expires_at: datetime) -> None:
        self._sessions().insert_one(
            {"user_id": user_id, "token_hash": token_hash, "created_at": utcnow(), "expires_at": expires_at}
        )

    def find_valid_session(self, token_hash: str) -> Optional[Dict[str, Any]]:
        return self._sessions().find_one({"token_hash": token_hash, "expires_at": {"$gt": utcnow()}})

    def delete_session(self, token_hash: str) -> None:
        self._sessions().delete_one({"token_hash": token_hash})


user_repository = UserRepository()
