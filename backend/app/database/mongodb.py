import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    """
    Get or create the singleton MongoClient instance with short timeouts.
    Does not crash at import time if MongoDB is unavailable.
    """
    global _client
    if _client is None:
        _client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=5000,
        )
    return _client


def get_database() -> Database:
    """Retrieve the application MongoDB database."""
    client = get_mongo_client()
    return client[settings.mongodb_database]


def get_syllabus_collection() -> Collection:
    """Retrieve the 'syllabi' collection from the database."""
    return get_database()["syllabi"]


def check_database_connection() -> bool:
    """
    Check if the MongoDB server is reachable without exposing credentials.
    Returns True if ping command succeeds, False otherwise.
    """
    try:
        client = get_mongo_client()
        client.admin.command("ping")
        return True
    except Exception as err:
        logger.warning(f"MongoDB connection check failed: {err}")
        return False


def close_database_connection() -> None:
    """Close the MongoClient connection during application shutdown."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception as err:
            logger.warning(f"Error closing MongoDB connection: {err}")
        _client = None


def __getattr__(name: str):
    """
    Provide backward compatibility for code expecting top-level module attributes
    `client`, `database`, or `syllabus_collection`.
    """
    if name == "client":
        return get_mongo_client()
    if name == "database":
        return get_database()
    if name == "syllabus_collection":
        return get_syllabus_collection()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
