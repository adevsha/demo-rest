import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def init_mongo() -> AsyncIOMotorDatabase:
    global _client, _database
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    _database = _client.get_database(settings.MONGO_DB)
    await _database.command("ping")
    return _database


async def close_mongo() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None


def get_db() -> AsyncIOMotorDatabase:
    if _database is None:
        raise RuntimeError("MongoDB not initialized")
    return _database


async def next_sequence(name: str) -> int:
    db = get_db()
    result = await db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(result["seq"])
