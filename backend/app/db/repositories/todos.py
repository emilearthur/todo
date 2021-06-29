"""All functions to handle crud todos."""

from typing import List, Union

from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.todo import TodoCreate, TodoInDB, TodoPublic, TodoUpdate
from app.models.user import UserInDB
from databases import Database
from fastapi import HTTPException, status
from redis.client import Redis

CREATE_TODO_QUERY = """
    INSERT INTO todos (name, notes, priority, duedate, owner, as_task)
    VALUES (:name, :notes, :priority, :duedate, :owner, :as_task)
    RETURNING id, name, notes, priority, duedate, owner, created_at, updated_at, as_task;
"""

GET_TODO_BY_ID_QUERY = """
    SELECT id, name, notes, priority, duedate, owner, created_at, updated_at, as_task
    from todos
    WHERE id = :id;
"""

GET_ALL_TODOS_QUERY = """
    SELECT id, name, notes, priority, duedate, created_at, updated_at, as_task
    FROM todos
"""

UPDATE_TODO_BY_ID_QUERY = """
    UPDATE todos
    SET name        = :name,
        notes       = :notes,
        priority    = :priority,
        duedate     = :duedate,
        as_task     = :as_task
    WHERE id = :id
    RETURNING id, name, notes, priority, duedate, owner, created_at, updated_at, as_task;
"""

DELETE_TODO_BY_ID_QUERY = """
    DELETE FROM todos
    WHERE id = :id
    RETURNING id;
"""

LIST_ALL_USER_TODOS_QUERY = """
    SELECT id, name, notes, priority, duedate, owner, created_at, updated_at, as_task
    FROM todos
    WHERE owner = :owner;
"""


class TodosRepository(BaseRepository):
    """All db actions associated with the Todos resources."""

    def __init__(self, db: Database, r_db: Redis) -> None:
        """Initilizing database, redis and users_repository."""
        super().__init__(db, r_db)
        self.users_repo = UsersRepository(db, r_db)

    async def create_todo(self, *, new_todo: TodoCreate, requesting_user: UserInDB) -> TodoInDB:
        """Create todo."""
        todo = await self.db.fetch_one(query=CREATE_TODO_QUERY, values={**new_todo.dict(), "owner": requesting_user.id})
        return TodoInDB(**todo)

    async def get_todo_by_id(
        self, *, id: int, requesting_user: UserInDB, populate: bool = True
    ) -> Union[TodoInDB, TodoPublic]:
        """Get todo."""
        todo_record = await self.db.fetch_one(query=GET_TODO_BY_ID_QUERY, values={"id": id})
        if todo_record:
            todo = TodoInDB(**todo_record)
            if populate:
                return await self.populate_todo(todo=todo, requesting_user=requesting_user)
            return todo

    async def get_all_todos(self) -> List[TodoInDB]:
        """Get all todo."""
        todos = await self.db.fetch_all(query=GET_ALL_TODOS_QUERY)
        return [TodoInDB(**todo) for todo in todos]

    async def list_all_user_todos(self, *, requesting_user: UserInDB) -> List[TodoInDB]:
        """List all todo by user."""
        todo_records = await self.db.fetch_all(query=LIST_ALL_USER_TODOS_QUERY, values={"owner": requesting_user.id})
        return [TodoInDB(**todo) for todo in todo_records]

    async def update_todos_by_id(self, *, todo: TodoInDB, todo_update: TodoUpdate) -> TodoInDB:
        """Update todo with todo id."""
        todo_updated_params = todo.copy(update=todo_update.dict(exclude_unset=True))
        if todo_updated_params.priority is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid priority type, Cannot be None")

        todo_updated = await self.db.fetch_one(
            query=UPDATE_TODO_BY_ID_QUERY,
            values=todo_updated_params.dict(exclude={"owner", "created_at", "updated_at"}),
        )
        return TodoInDB(**todo_updated)

    async def delete_todo_by_id(self, *, todo: TodoInDB) -> int:
        """Delete todo via todo id."""
        return await self.db.execute(query=DELETE_TODO_BY_ID_QUERY, values={"id": todo.id})

    async def populate_todo(self, *, todo: TodoInDB, requesting_user: UserInDB = None) -> TodoPublic:
        """Populate todo with user."""
        return TodoPublic(
            **todo.dict(exclude={"owner"}),
            owner=await self.users_repo.get_user_by_id(user_id=todo.owner),
        )
