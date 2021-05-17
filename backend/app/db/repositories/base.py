"""Base Repository."""

from databases import Database
from redis.client import Redis


class BaseRepository:
    """Base class."""

    def __init__(self, db: Database, r_db: Redis) -> None:
        """Initialize. db (Database): Initalize database, r_db (Redis): Initalize redis."""
        self.db = db
        self.r_db = r_db
