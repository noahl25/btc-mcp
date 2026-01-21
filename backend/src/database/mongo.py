from dotenv import load_dotenv
from pymongo import AsyncMongoClient
import os
from ..utils.logging import get_logger

load_dotenv()
_CLIENT: AsyncMongoClient | None = None
_DB = None
_LOGGER = get_logger(__name__)

async def connect_db():
    global _CLIENT, _DB
    try:
        _CLIENT = AsyncMongoClient(os.getenv("MONGO"))
        await _CLIENT.admin.command("ping")
        _DB = _CLIENT["main"]
        _LOGGER.info("MongoDB connected successfully!")
    except Exception as e:
        _LOGGER.exception("Error connecting to MongoDB", exc_info=True)
        raise

async def close_db():
    global _CLIENT
    if _CLIENT:
        await _CLIENT.close()
        _CLIENT = None
        _LOGGER.info("MongoDB connection closed!")

def get_db():
    global _DB
    if _DB is not None:
        return _DB
    raise RuntimeError("MongoDB not connected.")
