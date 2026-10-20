"""
Repository for syllabus persistence in MongoDB.
Encapsulates CRUD operations on the 'syllabi' collection.
"""

import logging
from typing import Any, Dict, List, Optional
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from pymongo import ReturnDocument

from app.database.mongodb import get_syllabus_collection
from app.models.syllabus import get_utc_now_iso, parse_object_id, serialize_mongo_doc

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when MongoDB is unreachable or operations fail due to connection issues."""
    pass


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
        """
        Insert a new syllabus document into MongoDB.
        Sets created_at and updated_at UTC timestamps.
        """
        now = get_utc_now_iso()
        doc = dict(syllabus_data)
        doc.setdefault("created_at", now)
        doc["updated_at"] = now
        doc.setdefault("processing_status", "reviewed")

        try:
            result = self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
            return serialize_mongo_doc(doc)
        except PyMongoError as err:
            logger.error(f"MongoDB insert_one error: {err}")
            raise DatabaseConnectionError(f"Database insert error: {err}") from err

    def get_by_id(self, syllabus_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a syllabus document by its string ObjectId.
        Returns None if ID is invalid or document does not exist.
        """
        oid = parse_object_id(syllabus_id)
        if oid is None:
            return None

        try:
            doc = self.collection.find_one({"_id": oid})
            if doc is None:
                return None
            return serialize_mongo_doc(doc)
        except PyMongoError as err:
            logger.error(f"MongoDB find_one error for ID '{syllabus_id}': {err}")
            raise DatabaseConnectionError(f"Database query error: {err}") from err

    def list_all(self, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """
        List saved syllabus records ordered by last updated date descending.
        """
        try:
            cursor = (
                self.collection.find()
                .sort("updated_at", -1)
                .skip(skip)
                .limit(limit)
            )
            return [serialize_mongo_doc(doc) for doc in cursor]
        except PyMongoError as err:
            logger.error(f"MongoDB find error: {err}")
            raise DatabaseConnectionError(f"Database listing error: {err}") from err

    def update(self, syllabus_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing syllabus by its ObjectId.
        Automatically updates updated_at timestamp.
        """
        oid = parse_object_id(syllabus_id)
        if oid is None:
            return None

        clean_update = {k: v for k, v in update_data.items() if v is not None and k not in ("_id", "id")}
        clean_update["updated_at"] = get_utc_now_iso()

        try:
            updated_doc = self.collection.find_one_and_update(
                {"_id": oid},
                {"$set": clean_update},
                return_document=ReturnDocument.AFTER,
            )
            if updated_doc is None:
                return None
            return serialize_mongo_doc(updated_doc)
        except PyMongoError as err:
            logger.error(f"MongoDB update error for ID '{syllabus_id}': {err}")
            raise DatabaseConnectionError(f"Database update error: {err}") from err

    def delete(self, syllabus_id: str) -> bool:
        """
        Delete a syllabus document by its ObjectId.
        Returns True if deleted, False if not found.
        """
        oid = parse_object_id(syllabus_id)
        if oid is None:
            return False

        try:
            result = self.collection.delete_one({"_id": oid})
            return result.deleted_count > 0
        except PyMongoError as err:
            logger.error(f"MongoDB delete error for ID '{syllabus_id}': {err}")
            raise DatabaseConnectionError(f"Database deletion error: {err}") from err


syllabus_repository = SyllabusRepository()
