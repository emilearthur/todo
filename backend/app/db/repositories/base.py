from databases import Database
from redis.client import Redis


class BaseRepository:
    def __init__(self, db: Database, r_db: Redis) -> None:
        self.db = db
        self.r_db = r_db
