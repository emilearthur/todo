import datetime
from typing import List

import pytest

from httpx import AsyncClient
from fastapi import FastAPI, status

from app.models.todo import TodoCreate, TodoInDB
from fastapi.encoders import jsonable_encoder

# decorate all test with @pytest.mark.asyncio
pytestmark = pytest.mark.asyncio


class TestTodosRoute:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.post(app.url_path_for("todos:create-todo"), json={})
        assert res.status_code != status.HTTP_404_NOT_FOUND

    async def test_invalid_input_raises_error(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.post(app.url_path_for("todos:create-todo"), json={})
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreateTodo:
    async def test_valid_input_create_todo(self, app: FastAPI, client: AsyncClient,
                                           new_todo: TodoCreate) -> None:
        res = await client.post(app.url_path_for("todos:create-todo"),
                                json={"new_todo": jsonable_encoder(new_todo.dict())})
        assert res.status_code == status.HTTP_201_CREATED
        created_todo = TodoCreate(**res.json())
        assert created_todo == new_todo

    @pytest.mark.parametrize(
        "invalid_payload, status_code",
        (
            (None, 422),
            ({}, 422),
            ({"name": "test_name"}, 422),
            ({"priority": "critical"}, 422),
            ({"name": "test_name", "notes": "test notes"}, 422),
        ),
    )
    async def test_invalid_input_raises_error(self, app: FastAPI, client: AsyncClient,
                                              invalid_payload: dict, status_code: int) -> None:
        res = await client.post(app.url_path_for("todos:create-todo"),
                                json={"new_todo": jsonable_encoder(invalid_payload)})
        assert res.status_code == status_code


class TestGetTodo:
    async def test_get_todo_by_id(self, app: FastAPI,
                                  client: AsyncClient, test_todo: TodoCreate) -> None:
        res = await client.get(app.url_path_for("todos:get-todo-by-id", id=test_todo.id))
        assert res.status_code == status.HTTP_200_OK
        todo = TodoInDB(**res.json())
        assert todo == test_todo

    @pytest.mark.parametrize(
        "id, status_code",
        (
            (500, 404),
            (-1, 422),
            (None, 422),
        ),
    )
    async def test_wrong_id_returns_error(self, app: FastAPI,
                                          client: AsyncClient,
                                          id: int,
                                          status_code: int) -> None:
        res = await client.get(app.url_path_for("todos:get-todo-by-id", id=id))
        assert res.status_code == status_code

    async def test_get_all_todos_return_valid_response(self, app: FastAPI,
                                                       client: AsyncClient,
                                                       test_todo: TodoInDB) -> None:
        res = await client.get(app.url_path_for("todos:get-all-todos"))
        assert res.status_code == status.HTTP_200_OK
        assert isinstance(res.json(), list)
        assert len(res.json()) > 0
        todos = [TodoInDB(**todo) for todo in res.json()]
        assert test_todo in todos


class TestUpdateTodo:
    @pytest.mark.parametrize(
        "attrs_to_change, values",
        (
            (["name"], ["new fake todo name"]),
            (["notes"], ["new kind of todo list"]),
            (["priority"], ["standard"]),
            (["name", "notes"], ["some more todos", "some extra fake description"]),
            (["duedate", "priority"], [(datetime.date.today() + datetime.timedelta(days=5)), "standard"]),
        ),
    )
    async def test_update_todo_with_valid_input(self, app: FastAPI,
                                                client: AsyncClient,
                                                test_todo: TodoInDB,
                                                attrs_to_change: List[str],
                                                values: List[str]) -> None:
        todo_update = {"todo_update": {attrs_to_change[i]: values[i] for i in range(len(attrs_to_change))}}
        res = await client.put(app.url_path_for("todos:update-todo-by-id", id=test_todo.id),
                               json=jsonable_encoder(todo_update))
        assert res.status_code == status.HTTP_200_OK
        updated_todo = TodoInDB(**res.json())  # make sure it's the same todo
        for i in range(len(attrs_to_change)):    # making sure that any attribute updated changed to the correct value
            assert getattr(updated_todo, attrs_to_change[i]) != getattr(test_todo, attrs_to_change[i])
            assert getattr(updated_todo, attrs_to_change[i]) == values[i]
        # making sure no attributes values have changed
        for attr, value in updated_todo.dict().items():
            if attr not in attrs_to_change:
                assert getattr(test_todo, attr) == value

    @pytest.mark.parametrize(
        "id, payload, status_code",
        (
            (-1, {"name": "test"}, 422),
            (0, {"name": "test2"}, 422),
            (5000, {"name": "test3"}, 404),
            (1, None, 422),
            (1, {"priority": "invalid priority type"}, 422),
            (1, {"priority": None}, 400),
        ),
    )
    async def test_update_cleaning_with_invalid_input_throws_error(self, app: FastAPI,
                                                                   client: AsyncClient,
                                                                   id: int,
                                                                   payload: dict,
                                                                   status_code: int,) -> None:
        todo_update = {"todo_update": payload}
        res = await client.put(app.url_path_for("todos:update-todo-by-id", id=id),
                               json=todo_update)
        assert res.status_code == status_code


class TestDeleteTodo:
    async def test_can_delete_cleaning_successfully(self, app: FastAPI,
                                                    client: AsyncClient,
                                                    test_todo: TodoInDB) -> None:
        res = await client.delete(app.url_path_for("todos:delete-todo-by-id", id=test_todo.id))
        assert res.status_code == status.HTTP_200_OK
        # ensuring that todo is removed
        res = await client.get(app.url_path_for("todos:get-todo-by-id", id=test_todo.id))
        assert res.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "id, status_code",
        (
            (500, 404),
            (0, 422),
            (-1, 422),
            (None, 422),
        ),
    )
    async def test_can_delete_cleaning_invalid_throws_error(self, app: FastAPI,
                                                            client: AsyncClient,
                                                            test_todo: TodoInDB,
                                                            id: int,
                                                            status_code: int) -> None:
        res = await client.delete(app.url_path_for("todos:delete-todo-by-id", id=id))
        assert res.status_code == status_code
