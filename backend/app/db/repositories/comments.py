"""DB repo for comment."""

import logging
from typing import List

from app.db.repositories.base import BaseRepository
from app.db.repositories.tasks import TasksRepository
from app.db.repositories.todos import TodosRepository
from app.models.comment import CommentCreate, CommentInDB, CommentUpdate
from app.models.task import TaskInDB
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from databases import Database
from redis.client import Redis

logger = logging.getLogger(__name__)

CREATE_COMMENT_QUERY = """
    INSERT INTO comments (body, todo_id, comment_owner, task)
    VALUES (:body, :todo_id, :comment_owner, :task)
    RETURNING id, body, todo_id, comment_owner, created_at, updated_at;
"""


GET_COMMENTS_BY_ID_QUERY = """
    SELECT id, body, todo_id, comment_owner, created_at, updated_at
    FROM comments
    WHERE id= :id;
"""

GET_ALL_TODO_COMMENTS_QUERY = """
    SELECT id, body, todo_id, comment_owner, created_at, updated_at
    FROM comments
    WHERE todo_id = :todo_id
    AND task = 'False';
"""

GET_ALL_TASKS_COMMENTS_QUERY = """
    SELECT id, body, todo_id, comment_owner, created_at, updated_at
    FROM comments
    WHERE todo_id = :todo_id
    AND task = 'True';
"""

GET_ALL_USER_COMMENTS_QUERY = """
    SELECT id, body,todo_id, comment_owner, created_at, updated_at
    FROM comments
    WHERE comment_owner = :comment_owner;
"""

UPDATE_COMMENT_BY_ID_QUERY = """
    UPDATE comments
    SET body = :body
    WHERE id = :id
    RETURNING id, body, todo_id, comment_owner, created_at, updated_at;
"""

DELETE_COMMENT_BY_ID_QUERY = """
    DELETE FROM comments
    WHERE id =:id
    RETURNING id;
"""


class CommentsRepository(BaseRepository):
    """All db actions associated with the Comments resources."""

    def __init__(self, db: Database, r_db: Redis) -> None:
        """Initialize db to check todos."""
        super().__init__(db, r_db)
        self.todos_repo = TodosRepository(db, r_db)
        self.tasks_repo = TasksRepository(db, r_db)

    async def create_comment_todo(
        self, *, new_comment: CommentCreate, todo=TodoInDB, requesting_user: UserInDB
    ) -> CommentInDB:
        """Create comment for todo."""
        comment = await self.db.fetch_one(
            query=CREATE_COMMENT_QUERY,
            values={**new_comment.dict(), "todo_id": todo.id, "comment_owner": requesting_user.id},
        )
        return CommentInDB(**comment)

    async def create_comment_task(
        self, *, new_comment: CommentCreate, task=TaskInDB, requesting_user: UserInDB
    ) -> CommentInDB:
        """Create comment for task."""
        # check if todo exist
        comment = await self.db.fetch_one(
            query=CREATE_COMMENT_QUERY,
            values={**new_comment.dict(), "todo_id": task.todo_id, "comment_owner": requesting_user.id},
        )
        return CommentInDB(**comment)

    async def get_comments_by_id(self, *, id: int, requesting_user: UserInDB) -> CommentInDB:
        """Get comments by id."""
        comment = await self.db.fetch_one(query=GET_COMMENTS_BY_ID_QUERY, values={"id": id})
        if not comment:
            return None
        return CommentInDB(**comment)

    async def get_todo_comments(self, *, todo: TodoInDB) -> List[CommentInDB]:
        """Get all todos comments."""
        comments = await self.db.fetch_all(query=GET_ALL_TODO_COMMENTS_QUERY, values={"todo_id": todo.id})
        return [CommentInDB(**comment) for comment in comments]

    async def get_task_comments(self, *, task: TaskInDB) -> List[CommentInDB]:
        """Get all tasks comments."""
        comments = await self.db.fetch_all(query=GET_ALL_TASKS_COMMENTS_QUERY, values={"todo_id": task.todo_id})
        return [CommentInDB(**comment) for comment in comments]

    async def update_comments(self, *, comment: CommentInDB, comment_update: CommentUpdate) -> CommentInDB:
        """Update User comments."""
        comment_updated_params = comment.copy(update=comment_update.dict(exclude_unset=True))
        comment_updated = await self.db.fetch_one(
            query=UPDATE_COMMENT_BY_ID_QUERY,
            values=comment_updated_params.dict(exclude={"comment_owner", "created_at", "updated_at", "todo_id"}),
        )
        return CommentInDB(**comment_updated)

    async def delete_comment(self, *, comment: CommentInDB) -> int:
        """Delete a comment."""
        delete_comment_id = await self.db.execute(query=DELETE_COMMENT_BY_ID_QUERY, values={"id": comment.id})
        return delete_comment_id

    async def get_users_comments(self, *, requesting_user: UserInDB) -> List[CommentInDB]:
        """Get users comments."""
        comments = await self.db.fetch_all(
            query=GET_ALL_USER_COMMENTS_QUERY, values={"comment_owner": requesting_user.id}
        )
        print(comments)
        return [CommentInDB(**comment) for comment in comments]
