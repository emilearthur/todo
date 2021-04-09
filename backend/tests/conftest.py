import warnings
import os
import datetime

import pytest
from asgi_lifespan import LifespanManager

from fastapi import FastAPI
from httpx import AsyncClient
from databases import Database

import alembic
from alembic.config import Config

from app.db.repositories.todos import TodosRepository
from app.db.repositories.users import UsersRepository

from app.models.todo import TodoCreate, TodoInDB
from app.models.user import UserCreate, UserInDB

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
async def test_todo(db: Database) -> TodoInDB:
    todo_repo = TodosRepository(db)
    new_todo = TodoCreate(name="test todo",
                          notes="test notes",
                          priority="critical",
                          duedate=datetime.date.today())
    return await todo_repo.create_todo(new_todo=new_todo)


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
def authorized_client(client: AsyncClient, test_user: UserInDB) -> AsyncClient:
    access_token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
    client.headers = {**client.headers, "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}"}
    return client
