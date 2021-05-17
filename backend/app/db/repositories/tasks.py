"""DB repo for tasks."""

from typing import List

from app.db.repositories.base import BaseRepository
from app.models.task import TaskCreate, TaskInDB
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import HTTPException, status

CREATE_TASK_FOR_TODO_QUERY = """
    INSERT INTO user_task_for_todos (todo_id, user_id, status)
    VALUES (:todo_id, :user_id, :status)
    RETURNING todo_id, user_id, status, created_at, updated_at;
"""

LIST_OFFERS_FOR_TASK_QUERY = """
    SELECT todo_id, user_id, status, created_at, updated_at
    FROM user_task_for_todos
    WHERE todo_id = :todo_id;
"""

GET_OFFER_FOR_TASK_FROM_USER_QUERY = """
    SELECT todo_id, user_id, status, created_at, updated_at
    FROM user_task_for_todos
    WHERE todo_id = :todo_id AND user_id = :user_id;
"""

ACCEPT_OFFER_FOR_TASK_QUERY = """
    UPDATE user_task_for_todos
    SET status = 'accepted'
    WHERE todo_id = :todo_id AND user_id = :user_id
    RETURNING todo_id, user_id, status, created_at, updated_at;
"""

REJECT_ALL_OTHER_OFFERS_FOR_TASK_QUERY = """
    UPDATE user_task_for_todos
    SET status = 'rejected'
    WHERE todo_id = :todo_id
    AND user_id != :user_id
    AND status = 'pending';
"""

CANCEL_OFFER_FOR_TASK_QUERY = """
    UPDATE user_task_for_todos
    SET status = 'cancelled'
    WHERE todo_id = :todo_id AND user_id = :user_id
    RETURNING todo_id, user_id, status, created_at, updated_at;
"""

SET_ALL_OTHER_OFFERS_FOR_TASK_AS_PENDING_QUERY = """
    UPDATE user_task_for_todos
    SET status = 'pending'
    WHERE todo_id = :todo_id
    AND user_id != :user_id
    AND status = 'rejected';
"""

RESCIND_OFFER_FOR_TASK_QUERY = """
    DELETE FROM user_task_for_todos
    WHERE todo_id = :todo_id
    AND user_id = :user_id
"""

MARK_TASK_COMPLETE_QUERY = """
    UPDATE user_task_for_todos
    SET status = 'completed'
    WHERE todo_id = :todo_id AND user_id = :user_id;
"""


class TasksRepository(BaseRepository):
    """class for tasks."""

    async def set_task_for_todo_for_user(self, *, todo: TodoInDB, task_taker: UserInDB):
        """Set a task for user and accept."""
        if await self.get_offer_for_task_from_user(todo=todo, user=task_taker):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Users aren't allowed set a todo task more than once",
            )
        await self.create_task_for_todo(new_task=TaskCreate(todo_id=todo.id, user_id=task_taker.id))
        task = await self.get_offer_for_task_from_user(todo=todo, user=task_taker)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        accepted_task = await self.accept_offer_for_task(task=task)
        return accepted_task

    async def create_task_for_todo(self, *, new_task: TaskCreate) -> TaskInDB:
        """Create a task of a todo."""
        created_task = await self.db.fetch_one(
            query=CREATE_TASK_FOR_TODO_QUERY, values={**new_task.dict(), "status": "pending"}
        )
        return TaskInDB(**created_task)

    async def list_offers_for_task(self, *, todo: TodoInDB) -> List[TaskInDB]:
        """Get all offers of a task from the db."""
        tasks = await self.db.fetch_all(query=LIST_OFFERS_FOR_TASK_QUERY, values={"todo_id": todo.id})
        return [TaskInDB(**task) for task in tasks]

    async def get_offer_for_task_from_user(self, *, todo: TodoInDB, user: UserInDB) -> TaskInDB:
        """Get an offer for a task from db."""
        task_record = await self.db.fetch_one(
            query=GET_OFFER_FOR_TASK_FROM_USER_QUERY, values={"todo_id": todo.id, "user_id": user.id}
        )
        if not task_record:
            return None

        return TaskInDB(**task_record)

    async def accept_offer_for_task(self, *, task: TaskInDB) -> TaskInDB:
        """Accept offer for  a task."""
        async with self.db.transaction():
            accepted_task = await self.db.fetch_one(
                query=ACCEPT_OFFER_FOR_TASK_QUERY,
                values={"todo_id": task.todo_id, "user_id": task.user_id},
            )
            await self.db.execute(
                query=REJECT_ALL_OTHER_OFFERS_FOR_TASK_QUERY, values={"todo_id": task.todo_id, "user_id": task.user_id}
            )
            return TaskInDB(**accepted_task)

    async def cancel_offer_for_task(self, *, task: TaskInDB) -> TaskInDB:
        """Cancel offer for a task."""
        async with self.db.transaction():
            cancelled_task = await self.db.fetch_one(
                query=CANCEL_OFFER_FOR_TASK_QUERY, values={"todo_id": task.todo_id, "user_id": task.user_id}
            )
            await self.db.execute(
                query=SET_ALL_OTHER_OFFERS_FOR_TASK_AS_PENDING_QUERY,
                values={"todo_id": task.todo_id, "user_id": task.user_id},
            )
            return TaskInDB(**cancelled_task)

    async def rescind_offer_for_task(self, *, task: TaskInDB) -> int:
        """Rescind offer for a task."""
        return await self.db.execute(
            query=RESCIND_OFFER_FOR_TASK_QUERY,
            values={"todo_id": task.todo_id, "user_id": task.user_id},
        )

    async def mark_task_completed(self, *, todo: TodoInDB, tasktaker: UserInDB) -> TaskInDB:
        """Check task as complete."""
        return await self.db.fetch_one(
            query=MARK_TASK_COMPLETE_QUERY, values={"todo_id": todo.id, "user_id": tasktaker.id}
        )
