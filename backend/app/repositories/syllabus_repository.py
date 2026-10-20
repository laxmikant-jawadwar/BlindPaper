"""
Repository for syllabus persistence in MongoDB.
Every syllabus belongs to the faculty member who uploaded it (owner_id).
"""

import logging
from typing import Any, Dict, List, Optional

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.database.mongodb import get_syllabus_collection
from app.models.mongo import get_utc_now_iso, parse_object_id, serialize_mongo_doc
from app.repositories.errors import DatabaseConnectionError

logger = logging.getLogger(__name__)


class SyllabusRepository:
    """Encapsulates all database operations for syllabus documents."""

    def __init__(self, collection_provider=get_syllabus_collection):
        self._get_collection = collection_provider

    @property
    def collection(self) -> Collection:
        try:
            return self._get_collection()
        except Exception as err:
            logger.error(f"Failed to access syllabus collection: {err}")
            raise DatabaseConnectionError(f"Database connection error: {err}") from err

    def create(self, syllabus_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new syllabus document, stamping created_at and updated_at (UTC)."""
        now = get_utc_now_iso()
        doc = dict(syllabus_data)
        doc.setdefault("created_at", now)
        doc["updated_at"] = now

        try:
            doc["_id"] = self.collection.insert_one(doc).inserted_id
            return serialize_mongo_doc(doc)
        except PyMongoError as err:
            logger.error(f"MongoDB insert_one error: {err}")
            raise DatabaseConnectionError(f"Database insert error: {err}") from err

    def get_by_id(self, syllabus_id: str, owner_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch a syllabus by its ObjectId string. With owner_id, only that owner's syllabus is
        returned, so another faculty member's syllabus looks exactly like one that doesn't exist.
        """
        oid = parse_object_id(syllabus_id)
        if oid is None:
            return None

        query: Dict[str, Any] = {"_id": oid}
        if owner_id is not None:
            query["owner_id"] = owner_id
        try:
            doc = self.collection.find_one(query)
            return serialize_mongo_doc(doc) if doc else None
        except PyMongoError as err:
            logger.error(f"MongoDB find_one error for ID '{syllabus_id}': {err}")
            raise DatabaseConnectionError(f"Database query error: {err}") from err

    def list_for_owner(self, owner_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """A faculty member's syllabi, newest first."""
        try:
            cursor = self.collection.find({"owner_id": owner_id}).sort("created_at", -1).skip(skip).limit(limit)
            return [serialize_mongo_doc(doc) for doc in cursor]
        except PyMongoError as err:
            logger.error(f"MongoDB find error: {err}")
            raise DatabaseConnectionError(f"Database listing error: {err}") from err

    def delete(self, syllabus_id: str, owner_id: Optional[str] = None) -> bool:
        """Delete a syllabus. Returns False if it does not exist (or is not the owner's)."""
        oid = parse_object_id(syllabus_id)
        if oid is None:
            return False

        query: Dict[str, Any] = {"_id": oid}
        if owner_id is not None:
            query["owner_id"] = owner_id
        try:
            return self.collection.delete_one(query).deleted_count > 0
        except PyMongoError as err:
            logger.error(f"MongoDB delete error for ID '{syllabus_id}': {err}")
            raise DatabaseConnectionError(f"Database deletion error: {err}") from err


syllabus_repository = SyllabusRepository()
