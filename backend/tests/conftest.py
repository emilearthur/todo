import warnings
import os
import datetime

import pytest
from typing import List
from asgi_lifespan import LifespanManager

from fastapi import FastAPI
from httpx import AsyncClient
from databases import Database

import alembic
from alembic.config import Config

from app.db.repositories.todos import TodosRepository
from app.db.repositories.users import UsersRepository
from app.db.repositories.comments import CommentsRepository

from app.models.todo import TodoCreate, TodoInDB
from app.models.user import UserCreate, UserInDB
from app.models.comment import CommentCreate, CommentInDB

from app.core.config import SECRET_KEY, JWT_TOKEN_PREFIX
from app.services import auth_service


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
        async with AsyncClient(app=app,
                               base_url="http://testserver",
                               headers={"Content-Type": "application/json"}) as client:
            yield client


@pytest.fixture
def new_todo():
    return TodoCreate(name="test todo",
                      notes="test notes",
                      priority="critical",
                      duedate=datetime.date.today())


@pytest.fixture
async def test_todo(db: Database, test_user: UserInDB) -> TodoInDB:
    todo_repo = TodosRepository(db)
    new_todo = TodoCreate(name="test todo",
                          notes="test notes",
                          priority="critical",
                          duedate=datetime.date.today())
    return await todo_repo.create_todo(new_todo=new_todo, requesting_user=test_user)


@pytest.fixture
def new_comment(test_todo: TodoInDB):
    return CommentCreate(body="test comments",
                         todo_id=test_todo.id)


@pytest.fixture
async def test_comment(db: Database, test_user: UserInDB, test_todo: TodoInDB) -> CommentInDB:
    comments_repo = CommentsRepository(db)
    new_comment = CommentCreate(body="test comments",
                                todo_id=test_todo.id)
    return await comments_repo.create_comment(new_comment=new_comment, requesting_user=test_user)


@pytest.fixture
async def test_comment_2(db: Database, test_user2: UserInDB, test_todo: TodoInDB) -> CommentInDB:
    comments_repo = CommentsRepository(db)
    new_comment = CommentCreate(body="test comments",
                                todo_id=test_todo.id)
    return await comments_repo.create_comment(new_comment=new_comment, requesting_user=test_user2)


@pytest.fixture
async def test_user(db: Database,) -> UserInDB:
    new_user = UserCreate(email="frederickauthur@hotmail.com",
                          username="frederickauthur",
                          password="mypassword",)
    user_repo = UsersRepository(db)

    existing_user = await user_repo.get_user_by_email(email=new_user.email)
    if existing_user:
        return existing_user
    return await user_repo.register_new_user(new_user=new_user)


@pytest.fixture
async def test_user2(db: Database) -> UserInDB:
    new_user = UserCreate(email="emilextrig@hotmail.com",
                          username="emilextrig",
                          password="somepassword",)
    user_repo = UsersRepository(db)

    existing_user = await user_repo.get_user_by_email(email=new_user.email)
    if existing_user:
        return existing_user
    return await user_repo.register_new_user(new_user=new_user)


@pytest.fixture
def authorized_client(client: AsyncClient, test_user: UserInDB) -> AsyncClient:
    access_token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
    client.headers = {**client.headers, "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}"}
    return client


@pytest.fixture
async def test_todos_list(db: Database, test_user2: UserInDB) -> List[TodoInDB]:
    todo_repo = TodosRepository(db)
    return [await todo_repo.create_todo(
        new_todo=TodoCreate(name=f"test todo {i}",
                            notes="some notes", priority="critical",
                            duedate=datetime.date.today()),
        requesting_user=test_user2) for i in range(5)]


@pytest.fixture
async def test_comment_list(db: Database, test_user2: UserInDB, test_todos_list: List[TodoInDB]) -> List[CommentInDB]:
    comments_repo = CommentsRepository(db)
    return [await comments_repo.create_comment(
        new_comment=CommentCreate(body=f"test comment {i}",
                                  todo_id=test_todos_list[i].id),
        requesting_user=test_user2) for i in range(5)]
