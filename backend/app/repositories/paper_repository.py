"""MongoDB access for question papers."""

import logging
import re
from typing import Any, Dict, List, Optional

from pymongo.errors import PyMongoError

from app.core.constants import SUBMITTED_STATUSES
from app.database.mongodb import get_papers_collection
from app.models.mongo import get_utc_now_iso, parse_object_id, serialize_mongo_doc
from app.repositories.errors import DatabaseConnectionError

logger = logging.getLogger(__name__)


class PaperRepository:
    def __init__(self, collection_provider=get_papers_collection):
        self._collection = collection_provider

    def create(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        now = get_utc_now_iso()
        doc = {**paper, "created_at": now, "updated_at": now}
        try:
            doc["_id"] = self._collection().insert_one(doc).inserted_id
        except PyMongoError as err:
            raise DatabaseConnectionError(f"Database insert error: {err}") from err
        return serialize_mongo_doc(doc)

    def get(self, paper_id: str, faculty_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """One paper; with faculty_id only that faculty member's paper (someone else's looks missing)."""
        oid = parse_object_id(paper_id)
        if oid is None:
            return None
        query: Dict[str, Any] = {"_id": oid}
        if faculty_id is not None:
            query["faculty_id"] = faculty_id
        doc = self._collection().find_one(query)
        return serialize_mongo_doc(doc) if doc else None

    def list_for_faculty(self, faculty_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"faculty_id": faculty_id}
        if status:
            query["status"] = status
        return [serialize_mongo_doc(d) for d in self._collection().find(query).sort("created_at", -1)]

    def list_submitted(
        self, status: Optional[str] = None, department: Optional[str] = None, search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Papers an admin can see (everything that has left Draft), most recently submitted first."""
        query: Dict[str, Any] = {"status": status if status in SUBMITTED_STATUSES else {"$in": SUBMITTED_STATUSES}}
        if department:
            query["department"] = department
        if search:
            pattern = {"$regex": re.escape(search.strip()), "$options": "i"}
            query["$or"] = [{"course_name": pattern}, {"course_code": pattern}, {"faculty_name": pattern}]
        return [serialize_mongo_doc(d) for d in self._collection().find(query).sort("submitted_at", -1)]

    def list_all(self) -> List[Dict[str, Any]]:
        """Every paper, drafts included (for the faculty overview)."""
        return [serialize_mongo_doc(d) for d in self._collection().find({})]

    def update(self, paper_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        oid = parse_object_id(paper_id)
        if oid is None:
            return None
        self._collection().update_one({"_id": oid}, {"$set": {**fields, "updated_at": get_utc_now_iso()}})
        return self.get(paper_id)

    def delete(self, paper_id: str) -> bool:
        oid = parse_object_id(paper_id)
        return oid is not None and self._collection().delete_one({"_id": oid}).deleted_count > 0

    def list_reviewed_for_faculty(self, faculty_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        query = {"faculty_id": faculty_id, "reviewed_at": {"$ne": None}, "status": {"$in": ["Approved", "Rejected"]}}
        cursor = self._collection().find(query).sort("reviewed_at", -1).limit(limit)
        return [serialize_mongo_doc(d) for d in cursor]


paper_repository = PaperRepository()
