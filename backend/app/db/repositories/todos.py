from typing import List

from fastapi.exceptions import HTTPException
from starlette import status
from app.db.repositories.base import BaseRepository
from app.models.todo import TodoCreate, TodoUpdate, TodoInDB


CREATE_TODO_QUERY = """
    INSERT INTO todos (name, notes, priority, duedate)
    VALUES (:name, :notes, :priority, :duedate)
    RETURNING id, name, notes, priority, duedate, created_at;
"""

GET_TODO_BY_ID_QUERY = """
    SELECT id, name, notes, priority, duedate, created_at
    FROM todos
    WHERE id = :id;
"""

GET_ALL_TODOS_QUERY = """
    SELECT id, name, notes, priority, duedate, created_at
    FROM todos
"""

UPDATE_TODO_BY_ID_QUERY = """
    UPDATE todos
    SET name        = :name,
        notes       = :notes,
        priority    = :priority,
        duedate     = :duedate
    WHERE id = :id
    RETURNING id, name, notes, priority, duedate, created_at;
"""

DELETE_TODO_BY_ID_QUERY = """
    DELETE FROM todos
    WHERE id = :id
    RETURNING id;
"""


class TodosRepository(BaseRepository):
    """ All db actions associated with the Todos resources """
    async def create_todo(self, *, new_todo: TodoCreate) -> TodoInDB:
        query_values = new_todo.dict()
        todo = await self.db.fetch_one(query=CREATE_TODO_QUERY, values=query_values)
        return TodoInDB(**todo)

    async def get_todo_by_id(self, *, id: int) -> TodoInDB:
        todo = await self.db.fetch_one(query=GET_TODO_BY_ID_QUERY, values={"id": id})
        if not todo:
            return None
        return TodoInDB(**todo)

    async def get_all_todos(self) -> List[TodoInDB]:
        todos = await self.db.fetch_all(query=GET_ALL_TODOS_QUERY)
        return [TodoInDB(**todo) for todo in todos]

    async def update_todos_by_id(self, *, id: int, todo_update: TodoUpdate) -> TodoInDB:
        todo = await self.get_todo_by_id(id=id)
        if not todo:
            return None
        todo_updated_params = todo.copy(update=todo_update.dict(exclude_unset=True))
        if todo_updated_params.priority is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid priority type, Cannot be None")
        try:
            todo_updated = await self.db.fetch_one(query=UPDATE_TODO_BY_ID_QUERY, values=todo_updated_params.dict())
            return TodoInDB(**todo_updated)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid update parameters.")

    async def delete_todo_by_id(self, *, id: int) -> int:
        todo = await self.get_todo_by_id(id=id)
        if not todo:
            return None

        deleted_todo_id = await self.db.execute(query=DELETE_TODO_BY_ID_QUERY, values={"id": id})
        return deleted_todo_id
