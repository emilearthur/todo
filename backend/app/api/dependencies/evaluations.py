"""Evaluation for Dependecies."""

from os import stat
from typing import List

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.tasks import get_offer_for_task_from_user_by_path
from app.api.dependencies.todos import get_todo_by_id_from_path
from app.api.dependencies.users import get_user_by_username_from_path
from app.db.repositories.evaluations import EvaluationsRepository
from app.models.evaluation import EvaluationInDB
from app.models.task import TaskInDB
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import Depends, HTTPException, Path, status


async def check_evaluation_create_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    todo: TodoInDB = Depends(get_todo_by_id_from_path),
    tasktaker: UserInDB = Depends(get_user_by_username_from_path),
    task: TaskInDB = Depends(get_offer_for_task_from_user_by_path),
    evals_repo: EvaluationsRepository = Depends(get_repository(EvaluationsRepository)),
) -> None:
    """Check user ability to create permisssions."""
    if todo.owner != current_user.id:  # check that only owners of a todo can leave evaluations for that task
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users are unable to leave evaluations for todo task they don't own.",
        )
    # only tasks accepted can be evaluated.
    if task.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only users accepted tasks can be evaluated."
        )
    # check that evaluations cna only be made for user whose offer for task was accepted for a job.
    if task.user_id != tasktaker.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You are not authorized to leave an this user."
        )
