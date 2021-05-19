"""Database Connect Tasks."""

import logging
import os

import aioredis
from app.core.config import DATABASE_URL, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from databases import Database
from fastapi import FastAPI

logger = logging.getLogger(__name__)


async def connect_to_db(app: FastAPI) -> None:
    """Connect to postgres db."""
    DB_URL = f"{DATABASE_URL}_test" if os.environ.get("TESTING") else DATABASE_URL
    database = Database(DB_URL, min_size=2, max_size=10)
    try:
        await database.connect()
        app.state._db = database
    except Exception as e:
        logger.warning("--- DB CONNECTION ERROR ---")
        logger.warning(e)
        logger.warning("--- DB CONNECTION ERROR ---")


async def close_db_connection(app: FastAPI) -> None:
    """Close to postgres db."""
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.warning("--- DB DISCONNECT ERROR ---")
        logger.warning(e)
        logger.warning("--- DB DISCONNECT ERROR ---")


async def connect_to_redis(app: FastAPI) -> None:
    """Connect to redis."""
    try:
        client = await aioredis.create_redis_pool(
            (REDIS_HOST, REDIS_PORT), db=0, password=str(REDIS_PASSWORD), timeout=10
        )
        # client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=str(REDIS_PASSWORD), db=0, socket_timeout=10)
        app.state._redis = client
    except Exception as e:
        logger.warning("--- Redis Authenication Error")
        logger.warning(e)
        logger.warning("--- Redis Authenication Error")


async def close_redis_connection(app: FastAPI) -> None:
    """Connect to redis."""
    try:
        await app.state._redis.close()
    except Exception as e:
        logger.warn("--- DB DISCONNECT ERROR ---")
        logger.warn(e)
        logger.warn("--- DB DISCONNECT ERROR ---")
