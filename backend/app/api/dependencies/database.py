"""Dependency for db and redis."""

from typing import Callable, Type

from app.db.repositories.base import BaseRepository
from databases import Database
from fastapi import Depends
from redis.client import Redis
from starlette.requests import Request


def get_database(request: Request) -> Database:
    """Get db from app state."""
    return request.app.state._db


def get_database_redis(request: Request) -> Redis:
    """Get redis from app state."""
    return request.app.state._redis


def get_repository(Repo_type: Type[BaseRepository]) -> Callable:
    """Dependency for redis and db."""

    def get_repo(
        db: Database = Depends(get_database), redis: Redis = Depends(get_database_redis)
    ) -> Type[BaseRepository]:
        return Repo_type(db, redis)

    return get_repo
