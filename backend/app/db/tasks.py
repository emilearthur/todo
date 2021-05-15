import logging
import os

import redis
from app.core.config import DATABASE_URL, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from databases import Database
from fastapi import FastAPI

logger = logging.getLogger(__name__)


async def connect_to_db(app: FastAPI) -> None:
    DB_URL = f"{DATABASE_URL}_test" if os.environ.get("TESTING") else DATABASE_URL
    database = Database(DB_URL, min_size=2, max_size=10)
    try:
        await database.connect()
        app.state._db = database
    except Exception as e:
        logger.warn("--- DB CONNECTION ERROR ---")
        logger.warn(e)
        logger.warn("--- DB CONNECTION ERROR ---")


async def close_db_connection(app: FastAPI) -> None:
    try:
        await app.state._db.disconnect()
    except Exception as e:
        logger.warn("--- DB DISCONNECT ERROR ---")
        logger.warn(e)
        logger.warn("--- DB DISCONNECT ERROR ---")


async def connect_to_redis(app: FastAPI) -> None:
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=str(REDIS_PASSWORD), db=0, socket_timeout=10)
        ping = client.ping()
        if ping is True:
            print("Redis connected")
            app.state._redis = client
    except redis.AuthenticationError as ae:
        logger.warn("--- Redis Authenication Error")
        logger.warn(ae)
        logger.warn("--- Redis Authenication Error")
