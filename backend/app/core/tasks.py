"""Core task: Connect and Disconnect to db and redis when application starts and stops."""
from typing import Callable

from app.db.tasks import close_db_connection, close_redis_connection, connect_to_db, connect_to_redis
from fastapi import FastAPI


def create_start_app_handler(app: FastAPI) -> Callable:
    """Connect to redis and db."""

    async def start_app() -> None:
        await connect_to_db(app)
        await connect_to_redis(app)

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable:
    """Disconnect to redis and db."""

    async def stop_app() -> None:
        await close_db_connection(app)
        await close_redis_connection(app)

    return stop_app
