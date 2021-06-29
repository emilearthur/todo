"""Test for evaluations."""

from statistics import mean
from typing import Callable, List

import pytest
from app.models.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationInDB
from app.models.todo import TodoInDB
from app.models.user import UserInDB
from fastapi import FastAPI, status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestEvaluationRoutes:
    """Test Evaluations."""

    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        """Testing evaluation routes."""
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
    """Testing Create Evaluation Route."""

    async def test_owner_can_leave_evaluation_for_tasktaker_for_task_completed(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user2: UserInDB,
        test_user3: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Only owner can leave evaluation for task tasker for completed task."""
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
        """Non owner of task cannot create review."""
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
        """Task cannot review wrong user."""
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

    async def test_owner_cant_leave_multiple_reviews(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user3: UserInDB,
        test_user2: UserInDB,
        test_todo_with_accepted_task_offer: TodoInDB,
    ) -> None:
        """Task owner cannot give multiple reviews."""
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


class TestGetEvaluation:
    """Test Get Evaluation Route."""

    async def test_authenticated_user_can_get_evaluation_for_todo(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user3: UserInDB,
        test_user4: UserInDB,
        test_list_of_todos_with_evaluated_task: List[TodoInDB],
    ) -> None:
        """Test authenticated user who is not owner or tasktaker can single evaluation."""
        authorized_client = create_authorized_client(user=test_user4)
        res = await authorized_client.get(
            app.url_path_for(
                "evaluations:get-evaluation-for-tasktaker",
                todo_id=test_list_of_todos_with_evaluated_task[0].id,
                username=test_user3.username,
            )
        )
        assert res.status_code == status.HTTP_200_OK
        evaluation = EvaluationInDB(**res.json())
        assert evaluation.todo_id == test_list_of_todos_with_evaluated_task[0].id
        assert evaluation.tasktaker_id == test_user3.id
        assert "testing some headline here" in evaluation.headline
        assert "testing some comment here" in evaluation.comment
        assert evaluation.professionalism >= 0 and evaluation.professionalism <= 5
        assert evaluation.completeness >= 0 and evaluation.completeness <= 5
        assert evaluation.efficiency >= 0 and evaluation.efficiency <= 5
        assert evaluation.overall_rating >= 0 and evaluation.overall_rating <= 5

    async def test_authenticated_user_can_get_list_of_evaluation_for_tasktaker(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user3: UserInDB,
        test_user4: UserInDB,
        test_list_of_todos_with_evaluated_task: List[TodoInDB],
    ) -> None:
        """Test authenticated user can fetech all of a tasktakers's evaluations."""
        authorized_client = create_authorized_client(user=test_user4)
        res = await authorized_client.get(
            app.url_path_for("evaluations:list-evaluation-for-tasktaker", username=test_user3.username)
        )
        assert res.status_code == status.HTTP_200_OK
        evaluations = [EvaluationInDB(**evaluation) for evaluation in res.json()]
        assert len(evaluations) > 1
        for evaluation in evaluations:
            assert evaluation.tasktaker_id == test_user3.id
            assert evaluation.overall_rating >= 0

    async def test_authenticated_user_can_get_aggregate_stats_for_tasktaker(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_user3: UserInDB,
        test_user4: UserInDB,
        test_list_of_todos_with_evaluated_task: List[TodoInDB],
    ) -> None:
        """Test that tasktaker evaluations comes with an aggregate."""
        authorized_client = create_authorized_client(user=test_user4)
        res = await authorized_client.get(
            app.url_path_for("evaluations:list-evaluation-for-tasktaker", username=test_user3.username)
        )
        assert res.status_code == status.HTTP_200_OK
        evaluations = [EvaluationInDB(**evaluation) for evaluation in res.json()]

        res = await authorized_client.get(
            app.url_path_for("evaluations:get-stats-for-tasktaker", username=test_user3.username)
        )
        assert res.status_code == status.HTTP_200_OK
        stats = EvaluationAggregate(**res.json())

        assert len(evaluations) == stats.total_evaluations
        assert max([e.overall_rating for e in evaluations]) == stats.max_overall_rating
        assert min([e.overall_rating for e in evaluations]) == stats.min_overall_rating
        assert mean([e.overall_rating for e in evaluations]) == stats.avg_overall_rating
        assert (
            mean([e.professionalism for e in evaluations if e.professionalism is not None]) == stats.avg_professionalism
        )
        assert mean([e.completeness for e in evaluations if e.completeness is not None]) == stats.avg_completeness
        assert mean([e.efficiency for e in evaluations if e.efficiency is not None]) == stats.avg_efficiency
        assert len([e for e in evaluations if e.overall_rating == 1]) == stats.one_stars
        assert len([e for e in evaluations if e.overall_rating == 2]) == stats.two_stars
        assert len([e for e in evaluations if e.overall_rating == 3]) == stats.three_stars
        assert len([e for e in evaluations if e.overall_rating == 4]) == stats.four_stars
        assert len([e for e in evaluations if e.overall_rating == 5]) == stats.five_stars

    async def test_authenticated_user_forbidden_from_get_request(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user3: UserInDB,
        test_list_of_todos_with_evaluated_task: List[TodoInDB],
    ) -> None:
        """Test that unauthorized user cannot get evaluations."""
        res = await client.get(
            app.url_path_for(
                "evaluations:get-evaluation-for-tasktaker",
                todo_id=test_list_of_todos_with_evaluated_task[0].id,
                username=test_user3.username,
            )
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
        res = await client.get(
            app.url_path_for("evaluations:list-evaluation-for-tasktaker", username=test_user3.username)
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
