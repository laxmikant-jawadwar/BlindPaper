from pymongo import MongoClient
from pymongo.collection import Collection

from app.core.config import settings

client = MongoClient(
    settings.mongodb_uri,
    serverSelectionTimeoutMS=5000,
)

database = client[settings.mongodb_database]
syllabus_collection: Collection = database["syllabi"]


def check_database_connection() -> bool:
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
