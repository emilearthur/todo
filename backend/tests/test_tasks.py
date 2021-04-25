"""Test for assigning todo."""

from typing import Callable, List

import pytest
from app.models.task import TaskCreate, TaskInDB, TaskPublic, TaskUpdate
from app.models.todo import TodoCreate, TodoInDB
from app.models.user import UserInDB
from databases import Database
from fastapi import FastAPI, status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestTaskRoutes:
    """Test to make sure task routes don't return 404s."""

    async def test_routes_exist(self, app: FastAPI, client: AsyncClient):
        """Making sure all routues are working."""
        res = await client.post(app.url_path_for("assigns:set-task", todo_id=1))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.post(app.url_path_for("assigns:create-task", todo_id=1))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.get(app.url_path_for("assigns:get_task_from_user", todo_id=1, username="johnmensah"))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.put(app.url_path_for("assigns:accept-task-from-user", todo_id=1, username="johnmensah"))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.put(app.url_path_for("assigns:cancel-task-from-user", todo_id=1))
        assert res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.delete(app.url_path_for("assigns:rescind-task-from-user", todo_id=1))
        res.status_code != status.HTTP_404_NOT_FOUND
        res = await client.get(app.url_path_for("assigns:list-tasks-for-todo", todo_id=1))
        assert res.status_code != status.HTTP_404_NOT_FOUND


class TestCreateTask:
    """Test creating tasks."""

    async def test_user_can_successfully_create_task_for_other_users_todo_task(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        test_todo: TodoInDB,
        test_user3: UserInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=test_user3)
        res = await authorized_client.post(app.url_path_for("assigns:create-task", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_201_CREATED
        task = TaskInDB(**res.json())
        assert task.user_id == test_user3.id
        assert task.todo_id == test_todo.id
        assert task.status == "pending"

    async def test_user_cant_create_duplicate_task(
        self, app: FastAPI, create_authorized_client: Callable, test_todo: TodoInDB, test_user4: UserInDB
    ) -> None:
        authorized_client = create_authorized_client(user=test_user4)
        res = await authorized_client.post(app.url_path_for("assigns:create-task", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_201_CREATED

        res = await authorized_client.post(app.url_path_for("assigns:create-task", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_user_unable_to_create_task_for_their_own_todo_job(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
        test_todo: TodoInDB,
    ) -> None:
        res = await authorized_client.post(app.url_path_for("assigns:create-task", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    async def test_unauthenticated_users_cant_create_todo(
        self, app: FastAPI, client: AsyncClient, test_todo: TodoInDB
    ) -> None:
        res = await client.post(app.url_path_for("assigns:create-task", todo_id=test_todo.id))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "id, status_code",
        (
            (50000000, 404),
            (-1, 422),
            (None, 422),
        ),
    )
    async def test_wrong_id_give_error_status(
        self, app: FastAPI, create_authorized_client: Callable, test_user5: UserInDB, id: int, status_code: int
    ) -> None:
        authorized_client = create_authorized_client(user=test_user5)
        res = await authorized_client.post(app.url_path_for("assigns:create-task", todo_id=id))
        assert res.status_code == status_code
