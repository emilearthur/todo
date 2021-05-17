"""Test for evaluations."""

from typing import Callable, List

import pytest
from app.models.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationInDB, EvaluationPublic
from app.models.task import TaskInDB
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import FastAPI, status
from httpx import AsyncClient
from pydantic.types import Json
from redis.client import Redis

pytestmark = pytest.mark.asyncio


class TestEvaluationRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.post(
            app.url_path_for("evaluations:create-evaluation-for-tasktaker", todo_id=1, username="emilextrig")
        )
        assert res.status_code != status.HTTP_404_NOT_FOUND

        res = await client.post(
            app.url_path_for("evaluations:get-evaluation-for-tasktaker", todo_id=1, username="emilextrig")
        )
        assert res.status_code != status.HTTP_404_NOT_FOUND

        res = await client.post(app.url_path_for("evaluations:list-evaluation-for-tasktaker", username="emilextrig"))
        assert res.status_code != status.HTTP_404_NOT_FOUND

        res = await client.post(app.url_path_for("evaluations:get-stats-for-tasktaker", username="emilextrig"))
        assert res.status_code != status.HTTP_404_NOT_FOUND


class TestCreateEvaluations:
    async def test_owner_can_leave_evaluation_for_tasktaker_for_task_completed(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        evaluation_create = EvaluationCreate(
            no_show=False,
            headline="Great Job",
            comment="Nice work and well done. Thanks very much. and great work",
            professionalism=5,
            completeness=5,
            efficiency=4,
            overall_rating=5,
        )
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-tasktaker",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"evaluation_create": evaluation_create.dict()},
        )
        assert res.status_code == status.HTTP_201_CREATED
        evaluation = EvaluationInDB(**res.json())
        assert evaluation.no_show == evaluation_create.no_show
        assert evaluation.headline == evaluation_create.headline
        assert evaluation.overall_rating == evaluation_create.overall_rating

        # check offer now been offered as "complete"
        res = await authorized_client.get(
            app.url_path_for(
                "assigns:get_offer_from_user",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            )
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["status"] == "completed"

    async def test_non_owner_cant_leave_review(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user4: UserInDB,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=test_user4)
        res = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-tasktaker",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user4.username,
            ),
            json={"evaluation_create": {"overall_rating": 2}},
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    async def test_owner_cant_leave_review_for_wrong_user(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user4: UserInDB,
        test_user2: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-tasktaker",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user4.username,
            ),
            json={"evaluation_create": {"overall_rating": 1}},
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_owner_cant_leave_review_for_wrong_user(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user3: UserInDB,
        test_user2: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=test_user2)
        res = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-tasktaker",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"evaluation_create": {"overall_rating": 3}},
        )
        assert res.status_code == status.HTTP_201_CREATED

        res = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-tasktaker",
                todo_id=test_todo_with_accepted_task_offer.id,
                username=test_user3.username,
            ),
            json={"evaluation_create": {"overall_rating": 1}},
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
