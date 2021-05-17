"""DB repo for evaluations."""

import logging
from typing import List

from app.db.repositories.base import BaseRepository
from app.db.repositories.tasks import TasksRepository
from app.models.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationInDB, EvaluationUpdate
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from databases import Database
from redis.client import Redis

logger = logging.getLogger(__name__)


CREATE_OWNER_EVALUATION_FOR_TASKTAKER_QUERY = """
    INSERT INTO task_to_tasktaker_evalations (
        todo_id,
        tasktaker_id,
        no_show,
        headline,
        comment,
        professionalism,
        completeness,
        efficiency,
        overall_rating)
    VALUES (
        :todo_id,
        :tasktaker_id,
        :no_show,
        :headline,
        :comment,
        :professionalism,
        :completeness,
        :efficiency,
        :overall_rating)
    RETURNING no_show,
              todo_id,
              tasktaker_id,
              headline,
              comment,
              professionalism,
              completeness,
              efficiency,
              overall_rating,
              created_at,
              updated_at;
"""


class EvaluationsRepository(BaseRepository):
    """class for evaluations."""

    def __init__(self, db: Database, r_db: Redis) -> None:
        """Initialize db and r_db and tasksrepository."""
        super().__init__(db, r_db)
        self.tasks_repo = TasksRepository(db, r_db)

    async def create_evaluation_for_task_taker(
        self, *, evaluation_create: EvaluationCreate, tasktaker: UserInDB, todo: TodoInDB
    ) -> EvaluationInDB:
        """Create an evaluation for a task."""
        async with self.db.transaction():
            created_evaluation = await self.db.fetch_one(
                query=CREATE_OWNER_EVALUATION_FOR_TASKTAKER_QUERY,
                values={**evaluation_create.dict(), "todo_id": todo.id, "tasktaker_id": tasktaker.id},
            )
            # also mark task as completed
            await self.tasks_repo.mark_task_completed(todo=todo, tasktaker=tasktaker)
            return EvaluationInDB(**created_evaluation)
