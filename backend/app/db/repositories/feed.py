"""DB repo for feeds."""

import datetime
import logging
from typing import List

from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.feed import TodoFeedItem
from app.models.user import UserInDB
from asyncpg import Record
from databases import Database
from redis.client import Redis

logger = logging.getLogger(__name__)

FETCH_TODO_JOBS_FOR_FEED_QUERY_old = """
SELECT id,
       name,
       notes,
       priority,
       duedate,
       owner,
       as_task,
       created_at,
       updated_at,
       CASE
            WHEN created_at = updated_at THEN 'is_create'
            ELSE 'is_update'
       END AS event_type,
       GREATEST(created_at, updated_at) AS event_timestamp,
       ROW_NUMBER() OVER ( ORDER BY GREATEST(created_at, updated_at) DESC ) AS row_number
FROM todos
WHERE as_task = TRUE
AND GREATEST(created_at, updated_at) < :starting_date
ORDER BY GREATEST(created_at, updated_at) DESC
LIMIT :page_chunk_size;
"""


FETCH_TODO_JOBS_FOR_FEED_QUERY = """
SELECT id,
       name,
       notes,
       priority,
       duedate,
       owner,
       as_task,
       created_at,
       updated_at,
       event_type,
       event_timestamp,
       ROW_NUMBER() OVER ( ORDER BY event_timestamp DESC ) AS row_number
       FROM (
           (
               SELECT  id,
                       name,
                       notes,
                       priority,
                       duedate,
                       owner,
                       as_task,
                       created_at,
                       updated_at,
                       updated_at AS event_timestamp,
                       'is_update' AS event_type
                FROM todos
                WHERE as_task = TRUE
                AND owner != :owner
                AND updated_at < :starting_date
                AND updated_at != created_at
                ORDER BY updated_at DESC
                LIMIT :page_chunk_size
           ) UNION(
               SELECT id,
                      name,
                      notes,
                      priority,
                      duedate,
                      owner,
                      as_task,
                      created_at,
                      updated_at,
                      created_at AS event_timestamp,
                      'is_create' AS event_type
                FROM todos
                WHERE as_task = TRUE
                AND owner != :owner
                AND created_at < :starting_date
                ORDER BY created_at DESC
                LIMIT :page_chunk_size
           )
       ) AS todo_feed
       ORDER BY event_timestamp DESC
       LIMIT :page_chunk_size;
"""


class FeedRepository(BaseRepository):
    """All db actions associated with the Feed resources."""

    def __init__(self, db: Database, r_db: Redis) -> None:
        """Initialize db and r_db and usersrepository."""
        super().__init__(db, r_db)
        self.users_repo = UsersRepository(db, r_db)

    async def fetch_todo_jobs_feed(
        self, *, requesting_user: UserInDB, page_chunk_size: int = 20, starting_date: datetime.datetime
    ) -> List[TodoFeedItem]:
        """Get all todo jobs."""
        todo_feed_item_records = await self.db.fetch_all(
            query=FETCH_TODO_JOBS_FOR_FEED_QUERY,
            values={"page_chunk_size": page_chunk_size, "starting_date": starting_date, "owner": requesting_user.id},
        )
        return [
            await self.populate_todo_feed_item(todo_feed_item=todo_feed_item)
            for todo_feed_item in todo_feed_item_records
        ]

    async def populate_todo_feed_item(self, *, todo_feed_item: Record) -> TodoFeedItem:
        """Get username to populate a todo feed."""
        return TodoFeedItem(
            **{k: v for k, v in todo_feed_item.items() if k != "owner"},
            owner=await self.users_repo.get_user_by_id(user_id=todo_feed_item["owner"])
        )
