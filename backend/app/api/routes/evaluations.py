"""Routes for evaluations."""

from typing import List

from app.api.dependencies.database import get_repository
from app.api.dependencies.evaluations import check_evaluation_create_permissions
from app.api.dependencies.todos import get_todo_by_id_from_path
from app.api.dependencies.users import get_user_by_username_from_path
from app.db.repositories.evaluations import EvaluationsRepository
from app.models.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationInDB, EvaluationPublic
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import APIRouter, Body, Depends, Path, status

router = APIRouter()


@router.post(
    "/{todo_id}/",
    response_model=EvaluationPublic,
    name="evaluations:create-evaluation-for-tasktaker",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_evaluation_create_permissions)],
)
async def create_evaluation_for_tasktaker(
    evaluation_create: EvaluationCreate = Body(..., embed=True),
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    tasktaker: UserInDB = Depends(get_user_by_username_from_path),
    evals_repo: EvaluationsRepository = Depends(get_repository(EvaluationsRepository)),
) -> EvaluationPublic:
    """Create Evaluations."""
    return await evals_repo.create_evaluation_for_task_taker(
        evaluation_create=evaluation_create, tasktaker=tasktaker, todo=todo
    )


@router.get(
    "/",
    response_model=List[EvaluationPublic],
    name="evaluations:list-evaluation-for-tasktaker",
)
async def list_evaluations_for_tasktaker() -> List[EvaluationPublic]:
    """List Evaluation for task taker."""
    return None


@router.get(
    "/stats/",
    response_model=EvaluationAggregate,
    name="evaluations:get-stats-for-tasktaker",
)
async def get_stats_for_tasktaker() -> EvaluationAggregate:
    """Get stats for task taker."""
    return None


@router.get(
    "/{todo_id}/",
    response_model=EvaluationPublic,
    name="evaluations:get-evaluation-for-tasktaker",
)
async def get_evaluation_for_tasktaker() -> EvaluationPublic:
    """Get evaluation for task taker."""
    return None
