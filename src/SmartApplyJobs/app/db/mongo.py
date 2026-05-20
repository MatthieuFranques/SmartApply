import os
from pymongo import MongoClient
from pymongo.database import Database

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            os.getenv("MONGODB_URI"),
            serverSelectionTimeoutMS=5000,
        )
    return _client


def get_db() -> Database:
    return get_client()[os.getenv("MONGODB_DB", "jobpipeline")]