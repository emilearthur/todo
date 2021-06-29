"""DB repo for evaluations."""

import logging
from typing import List

from app.db.repositories.base import BaseRepository
from app.db.repositories.tasks import TasksRepository
from app.models.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationInDB
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

GET_TASKTAKER_EVALUATION_FOR_TODO_QUERY = """
    SELECT no_show,
           todo_id,
           tasktaker_id,
           headline,
           comment,
           professionalism,
           completeness,
           efficiency,
           overall_rating,
           created_at,
           updated_at
    FROM task_to_tasktaker_evalations
    WHERE todo_id = :todo_id AND tasktaker_id = :tasktaker_id;
"""

LIST_EVALUATION_FOR_TASKTAKER_QUERY = """
    SELECT no_show,
           todo_id,
           tasktaker_id,
           headline,
           comment,
           professionalism,
           completeness,
           efficiency,
           overall_rating,
           created_at,
           updated_at
    FROM task_to_tasktaker_evalations
    WHERE tasktaker_id = :tasktaker_id;
"""

GET_TASKTAKER_AGGREGATE_RATINGS_QUERY = """
    SELECT
        AVG(professionalism) AS avg_professionalism,
        AVG(completeness) AS avg_completeness,
        AVG(efficiency) AS avg_efficiency,
        AVG(overall_rating) AS avg_overall_rating,
        MIN(overall_rating) AS min_overall_rating,
        MAX(overall_rating) AS max_overall_rating,
        COUNT(todo_id) AS total_evaluations,
        SUM(no_show::int) AS total_no_show,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 1) AS one_stars,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 2) AS two_stars,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 3) AS three_stars,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 4) AS four_stars,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 5) AS five_stars
    FROM task_to_tasktaker_evalations
    WHERE tasktaker_id = :tasktaker_id;
"""


class EvaluationsRepository(BaseRepository):
    """All db actions associated with the Evaluation resources."""

    def __init__(self, db: Database, r_db: Redis) -> None:
        """Initialize db and r_db and tasksrepository."""
        super().__init__(db, r_db)
        self.tasks_repo = TasksRepository(db, r_db)

    async def create_evaluation_for_tasktaker(
        self, *, evaluation_create: EvaluationCreate, tasktaker: UserInDB, todo: TodoInDB
    ) -> EvaluationInDB:
        """Create an evaluation for a task."""
        async with self.db.transaction():
            created_evaluation = await self.db.fetch_one(
                query=CREATE_OWNER_EVALUATION_FOR_TASKTAKER_QUERY,
                values={**evaluation_create.dict(), "todo_id": todo.id, "tasktaker_id": tasktaker.id},
            )
            # also mark task as complete
            await self.tasks_repo.mark_task_completed(todo=todo, tasktaker=tasktaker)
            return EvaluationInDB(**created_evaluation)

    async def get_tasktaker_evaluation_for_todo(self, *, todo: TodoInDB, tasktaker: UserInDB) -> EvaluationInDB:
        """Get evaluation for tasktaker."""
        evaluation = await self.db.fetch_one(
            query=GET_TASKTAKER_EVALUATION_FOR_TODO_QUERY,
            values={"todo_id": todo.id, "tasktaker_id": tasktaker.id},
        )
        if not evaluation:
            return None
        return EvaluationInDB(**evaluation)

    async def list_evaluations_for_tasktaker(self, *, tasktaker: UserInDB) -> List[EvaluationInDB]:
        """Get list of all evaluations of user."""
        evaluations = await self.db.fetch_all(
            query=LIST_EVALUATION_FOR_TASKTAKER_QUERY, values={"tasktaker_id": tasktaker.id}
        )
        return [EvaluationInDB(**evaluation) for evaluation in evaluations]

    async def get_tasktaker_aggregates(self, *, tasktaker: UserInDB) -> EvaluationAggregate:
        """Get tasktaker aggregates."""
        return await self.db.fetch_one(
            query=GET_TASKTAKER_AGGREGATE_RATINGS_QUERY, values={"tasktaker_id": tasktaker.id}
        )
