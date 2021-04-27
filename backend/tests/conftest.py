"""Confest module."""
import datetime
import os
import warnings
from typing import Callable, List

import alembic
import pytest
from alembic.config import Config
from app.core.config import JWT_TOKEN_PREFIX, SECRET_KEY
from app.db.repositories.comments import CommentsRepository
from app.db.repositories.tasks import TasksRepository
from app.db.repositories.todos import TodosRepository
from app.db.repositories.users import UsersRepository
from app.models.comment import CommentCreate, CommentInDB
from app.models.task import TaskCreate
from app.models.todo import TodoCreate, TodoInDB
from app.models.user import UserCreate, UserInDB
from app.services import auth_service
from asgi_lifespan import LifespanManager
from databases import Database
from fastapi import FastAPI
from httpx import AsyncClient


# apply migration at beginning and end of testing session
@pytest.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")
    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")


# create a new application for testing
@pytest.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.api.server import get_application

    return get_application()


# getting db
@pytest.fixture
def db(app: FastAPI) -> Database:
    return app.state._db


# make requests in our test
@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with LifespanManager(app):
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"Content-Type": "application/json"},
        ) as client:
            yield client


@pytest.fixture
def new_todo():
    return TodoCreate(
        name="test todo",
        notes="test notes",
        priority="critical",
        duedate=datetime.date.today(),
    )


@pytest.fixture
async def test_todo(db: Database, test_user: UserInDB) -> TodoInDB:
    todo_repo = TodosRepository(db)
    new_todo = TodoCreate(
        name="test todo",
        notes="test notes",
        priority="critical",
        duedate=datetime.date.today(),
    )
    return await todo_repo.create_todo(new_todo=new_todo, requesting_user=test_user)


@pytest.fixture
def new_comment(test_todo: TodoInDB):
    return CommentCreate(body="test comments", todo_id=test_todo.id)


@pytest.fixture
async def test_comment(db: Database, test_user: UserInDB, test_todo: TodoInDB) -> CommentInDB:
    comments_repo = CommentsRepository(db)
    new_comment = CommentCreate(body="test comments", todo_id=test_todo.id)
    return await comments_repo.create_comment(new_comment=new_comment, requesting_user=test_user)


@pytest.fixture
async def test_comment_2(db: Database, test_user2: UserInDB, test_todo: TodoInDB) -> CommentInDB:
    comments_repo = CommentsRepository(db)
    new_comment = CommentCreate(body="test comments", todo_id=test_todo.id)
    return await comments_repo.create_comment(new_comment=new_comment, requesting_user=test_user2)


# @pytest.fixture
# async def test_user(
#     db: Database,
# ) -> UserInDB:
#     new_user = UserCreate(
#         email="frederickauthur@hotmail.com",
#         username="frederickauthur",
#         password="mypassword",
#     )
#     user_repo = UsersRepository(db)

#     existing_user = await user_repo.get_user_by_email(email=new_user.email)
#     if existing_user:
#         return existing_user
#     return await user_repo.register_new_user(new_user=new_user)


# @pytest.fixture
# async def test_user2(db: Database) -> UserInDB:
#     new_user = UserCreate(
#         email="emilextrig@hotmail.com",
#         username="emilextrig",
#         password="somepassword",
#     )
#     user_repo = UsersRepository(db)

#     existing_user = await user_repo.get_user_by_email(email=new_user.email)
#     if existing_user:
#         return existing_user
#     return await user_repo.register_new_user(new_user=new_user)


@pytest.fixture
def authorized_client(client: AsyncClient, test_user: UserInDB) -> AsyncClient:
    access_token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}",
    }
    return client


@pytest.fixture
async def test_todos_list(db: Database, test_user2: UserInDB) -> List[TodoInDB]:
    todo_repo = TodosRepository(db)
    return [
        await todo_repo.create_todo(
            new_todo=TodoCreate(
                name=f"test todo {i}",
                notes="some notes",
                priority="critical",
                duedate=datetime.date.today(),
            ),
            requesting_user=test_user2,
        )
        for i in range(5)
    ]


@pytest.fixture
async def test_comment_list(db: Database, test_user2: UserInDB, test_todos_list: List[TodoInDB]) -> List[CommentInDB]:
    comments_repo = CommentsRepository(db)
    return [
        await comments_repo.create_comment(
            new_comment=CommentCreate(body=f"test comment {i}", todo_id=test_todos_list[i].id),
            requesting_user=test_user2,
        )
        for i in range(5)
    ]


@pytest.fixture
def create_authorized_client(client: AsyncClient) -> Callable:
    def _create_authorized_client(*, user: UserInDB) -> AsyncClient:
        access_token = auth_service.create_access_token_for_user(user=user, secret_key=str(SECRET_KEY))
        client.headers = {
            **client.headers,
            "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}",
        }
        return client

    return _create_authorized_client


async def user_fixture_helper(*, db: Database, new_user: UserCreate) -> UserInDB:
    users_repo = UsersRepository(db)
    existing_user = await users_repo.get_user_by_email(email=new_user.email)
    if existing_user:
        return existing_user
    return await users_repo.register_new_user(new_user=new_user)


@pytest.fixture
async def test_user(db: Database) -> UserInDB:
    new_user = UserCreate(email="frederickauthur@hotmail.com", username="frederickauthur", password="mypassword")
    return await user_fixture_helper(db=db, new_user=new_user)


@pytest.fixture
async def test_user2(db: Database) -> UserInDB:
    new_user = UserCreate(email="emilextrig@hotmail.com", username="emilextrig", password="somepassword")
    return await user_fixture_helper(db=db, new_user=new_user)


@pytest.fixture
async def test_user3(db: Database) -> UserInDB:
    new_user = UserCreate(email="jojo@gmail.com", username="jojo", password="morepassword")
    return await user_fixture_helper(db=db, new_user=new_user)


@pytest.fixture
async def test_user4(db: Database) -> UserInDB:
    new_user = UserCreate(email="akosua@hermail.com", username="akosua", password="moremorepassword")
    return await user_fixture_helper(db=db, new_user=new_user)


@pytest.fixture
async def test_user5(db: Database) -> UserInDB:
    new_user = UserCreate(email="janet@jackson.com", username="janet", password="somorepassword")
    return await user_fixture_helper(db=db, new_user=new_user)


@pytest.fixture
async def test_user6(db: Database) -> UserInDB:
    new_user = UserCreate(email="jay@cole.com", username="jaycole", password="jaycolepwd")
    return await user_fixture_helper(db=db, new_user=new_user)


@pytest.fixture
async def test_user_list(
    test_user3: UserInDB, test_user4: UserInDB, test_user5: UserInDB, test_user6: UserInDB
) -> List[UserInDB]:
    return [test_user3, test_user4, test_user5, test_user6]


@pytest.fixture
async def test_todo_with_tasks(db: Database, test_user2: UserInDB, test_user_list: List[UserInDB]) -> TodoInDB:
    todos_repo = TodosRepository(db)
    tasks_repo = TasksRepository(db)

    new_todo = TodoCreate(
        name="todo with an offer",
        notes="some notes",
        priority="critical",
        duedate=datetime.date.today(),
    )
    created_todo = await todos_repo.create_todo(new_todo=new_todo, requesting_user=test_user2)
    for user in test_user_list:
        await tasks_repo.create_task_for_todo(new_task=TaskCreate(todo_id=created_todo.id, user_id=user.id))
    return created_todo


@pytest.fixture
async def test_todo_with_accepted_offer(
    db: Database, test_user2: UserInDB, test_user3: UserInDB, test_user_list: List[UserInDB]
) -> TodoInDB:
    todos_repo = TodosRepository(db)
    tasks_repo = TasksRepository(db)

    new_todo = TodoCreate(
        name="todo with an offer",
        notes="some notes",
        priority="critical",
        duedate=datetime.date.today(),
    )
    created_todo = await todos_repo.create_todo(new_todo=new_todo, requesting_user=test_user2)

    tasks = []
    for user in test_user_list:
        tasks.append(
            await tasks_repo.create_task_for_todo(new_task=TaskCreate(todo_id=created_todo.id, user_id=user.id))
        )
    await tasks_repo.accept_task(task=[task for task in tasks if task.user_id == test_user3.id][0])
    return created_todo
