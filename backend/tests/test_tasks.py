"""Test for assigning todo."""

from typing import Callable, List

import pytest
from databases import Database
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.task import TaskCreate, TaskInDB, TaskPublic, TaskUpdate
from app.models.todo import TodoCreate, TodoInDB
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio


class TestAssignRoutes:
    """Test to make sure assign routes don't return 404s."""

    async def test_routes_exist(self, app: FastAPI, client: AsyncClient):
        """Making sure all routues are working."""
        res = await client.post(app.url_path_for("assigns:set-task-for-user", todi_id=1))
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
