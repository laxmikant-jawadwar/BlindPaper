"""
Domain models and conversion helpers for Syllabus documents stored in MongoDB.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from bson import ObjectId


def get_utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a MongoDB document for JSON serialization by converting
    `_id` ObjectId to a string `id`.
    """
    if not doc:
        return {}
    doc_copy = dict(doc)
    if "_id" in doc_copy:
        doc_copy["id"] = str(doc_copy.pop("_id"))
    elif "id" not in doc_copy:
        doc_copy["id"] = ""

    # Ensure datetime objects are converted to ISO strings
    if isinstance(doc_copy.get("created_at"), datetime):
        doc_copy["created_at"] = doc_copy["created_at"].isoformat()
    if isinstance(doc_copy.get("updated_at"), datetime):
        doc_copy["updated_at"] = doc_copy["updated_at"].isoformat()

    return doc_copy


def parse_object_id(id_str: str) -> Optional[ObjectId]:
    """Safely parse a string into a BSON ObjectId; returns None if invalid."""
    try:
        if ObjectId.is_valid(id_str):
            return ObjectId(id_str)
        return None
    except Exception:
        return None
