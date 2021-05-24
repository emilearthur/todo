from typing import Optional, Type, Union

import jwt
import pytest
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_AUDIENCE, SECRET_KEY

# from app.models.token import JWTMeta, JWTCreds, JWTPayload
from app.db.repositories.users import UsersRepository
from app.models.user import UserInDB, UserPublic
from app.services import auth_service
from databases import Database
from fastapi import FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from pydantic import ValidationError
from redis.client import Redis
from starlette.datastructures import Secret

pytestmark = pytest.mark.asyncio


class TestUserRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        new_user = {
            "email": "test@gmail.com",
            "username": "test_user",
            "password": "testpassword",
        }
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code != status.HTTP_404_NOT_FOUND


class TestUserRegistraton:
    async def test_users_can_register_successfully(
        self, app: FastAPI, client: AsyncClient, db: Database, r_db: Redis
    ) -> None:
        users_repo = UsersRepository(db, r_db)
        new_user = {
            "email": "emilepxx@gmail.com",
            "username": "emilepxxxtrig",
            "password": "testpassword1",
        }
        # making sure if user does not exist
        user_in_db = await users_repo.get_user_by_email(email=new_user["email"])
        assert user_in_db is None

        # send post request to create user and ensure it is successful
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code == status.HTTP_201_CREATED

        # ensure the user exits in db now
        user_in_db = await users_repo.get_user_by_email(email=new_user["email"], populate=False)
        assert user_in_db is not None
        assert user_in_db.email == new_user["email"]
        assert user_in_db.username == new_user["username"]

        # check the user returned in the response is equal to the user in the db
        created_user = UserPublic(**res.json()).dict(exclude={"access_token", "profile"})
        assert created_user == user_in_db.dict(exclude={"password", "salt"})

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("email", "emilepxx@gmail.com", 400),
            ("username", "emilepxxxtrig", 400),
            ("email", "invalid_email@one@two.io", 422),
            ("password", "sort", 422),
            ("username", "emilext@#$%^<>", 422),
            ("username", "ab", 422),
        ),
    )
    async def test_user_registeration_fails_when_credentials_are_taken(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Database,
        r_db: Redis,
        attr: str,
        value: str,
        status_code: int,
    ) -> None:
        new_user = {
            "email": "nottaken@email.io",
            "username": "not_taken_username",
            "password": "freepassword",
        }
        new_user[attr] = value
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code == status_code

    async def test_users_saved_password_is_hashed_and_has_salt(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Database,
        r_db: Redis,
    ) -> None:
        user_repo = UsersRepository(db, r_db)
        new_user = {
            "email": "frederickauthurxxx@hemile.io",
            "username": "fredeickauthuxxxr",
            "password": "gitpassword",
        }

        # post and ensure user was created
        res = await client.post(app.url_path_for("users:register-new-user"), json={"new_user": new_user})
        assert res.status_code == status.HTTP_201_CREATED

        # verify password is hashed in db and verifying auth
        user_in_db = await user_repo.get_user_by_email(email=new_user["email"], populate=False)
        assert user_in_db is not None
        assert user_in_db.salt is not None and user_in_db.salt != "123"
        assert user_in_db.password != new_user["password"]
        assert auth_service.verify_password(
            pwd=new_user["password"],
            salt=user_in_db.salt,
            hashed_pwd=user_in_db.password,
        )


class TestAuthTokens:
    async def test_can_create_access_token_successfully(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
    ) -> None:
        access_token = auth_service.create_access_token_for_user(
            user=test_user,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        creds = jwt.decode(
            access_token,
            str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            algorithms=[JWT_ALGORITHM],
        )
        assert creds.get("username") is not None
        assert creds["username"] == test_user.username
        assert creds["aud"] == JWT_AUDIENCE

    async def test_token_missing_user_is_invalid(self, app: FastAPI, client: AsyncClient) -> None:
        access_token = auth_service.create_access_token_for_user(
            user=None,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        with pytest.raises(jwt.PyJWTError):
            jwt.decode(
                access_token,
                str(SECRET_KEY),
                audience=JWT_AUDIENCE,
                algorithms=[JWT_ALGORITHM],
            )

    @pytest.mark.parametrize(
        "secret_key, jwt_audience, exception",
        (
            ("wrong-secret", JWT_AUDIENCE, jwt.InvalidSignatureError),
            (None, JWT_AUDIENCE, jwt.InvalidSignatureError),
            (SECRET_KEY, "othersite:auth", jwt.InvalidAudienceError),
            (SECRET_KEY, None, ValidationError),
        ),
    )
    async def test_invalid_token_content_raises_error(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
        secret_key: Union[str, Secret],
        jwt_audience: str,
        exception: Type[BaseException],
    ) -> None:
        with pytest.raises(exception):
            access_token = auth_service.create_access_token_for_user(
                user=test_user,
                secret_key=str(secret_key),
                audience=jwt_audience,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
            )
            jwt.decode(
                access_token,
                str(SECRET_KEY),
                audience=JWT_AUDIENCE,
                algorithms=[JWT_ALGORITHM],
            )

    async def test_can_get_username_from_token(self, app: FastAPI, client: AsyncClient, test_user: UserInDB) -> None:
        token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
        username = auth_service.get_username_from_token(token=token, secret_key=str(SECRET_KEY))
        assert username == test_user.username

    @pytest.mark.parametrize(
        "secret, wrong_token",
        (
            (SECRET_KEY, "asdf"),
            (SECRET_KEY, ""),
            (SECRET_KEY, None),
            ("ABC133", "use correct token"),
        ),
    )
    async def test_error_for_wrong_token_and_secret(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
        secret: Union[Secret, str],
        wrong_token: Optional[str],
    ) -> None:
        token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
        if wrong_token == "use correct token":
            wrong_token = token

        with pytest.raises(HTTPException):
            auth_service.get_username_from_token(token=wrong_token, secret_key=str(secret))


class TestUserLogin:
    async def test_user_can_login_successfully_and_get_valid_token(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {
            "username": test_user.email,
            "password": "mypassword",
        }

        res = await client.post(app.url_path_for("users:login-email-and-password"), data=login_data)
        assert res.status_code == status.HTTP_200_OK
        # check if tokoen exist in response and has user encoded within it
        token = res.json().get("access_token")
        creds = jwt.decode(token, str(SECRET_KEY), audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])
        assert "username" in creds
        assert creds["username"] == test_user.username
        assert "sub" in creds
        assert creds["sub"] == test_user.email
        # checking type of token
        assert "token_type" in res.json()
        assert res.json().get("token_type") == "bearer"

    @pytest.mark.parametrize(
        "credential, wrong_value, status_code",
        (
            ("email", "bademail@gmail.com", 401),
            ("email", None, 401),
            ("email", "notemail", 401),
            ("password", "wrongpwd", 401),
            ("password", None, 401),
        ),
    )
    async def test_user_with_wrong_creds_doesnt_get_token(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
        credential: str,
        wrong_value: str,
        status_code: int,
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        user_data = test_user.dict()
        user_data["password"] = "gitpassword"
        user_data[credential] = wrong_value
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"],
        }

        res = await client.post(app.url_path_for("users:login-email-and-password"), data=login_data)
        assert res.status_code == status_code
        assert "access_token" not in res.json()


class TestUserMe:
    async def test_authenicated_user_can_get_own_data(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
    ) -> None:
        res = await authorized_client.get(app.url_path_for("users:get-current-user"))
        assert res.status_code == status.HTTP_200_OK
        user = UserPublic(**res.json())
        assert user.username == test_user.username
        assert user.email == test_user.email
        assert user.id == test_user.id

    async def test_unauthenitcated_user_cannot_acccess_own_data(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: UserInDB,
    ) -> None:
        res = await client.get(app.url_path_for("users:get-current-user"))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "jwt_prefix",
        (
            ("",),
            ("value",),
            ("Token",),
            ("JWT",),
            ("Swearer",),
        ),
    )
    async def test_user_with_incorrect_jwt_prefix_cannot_access_own_data(
        self, app: FastAPI, client: AsyncClient, test_user: UserInDB, jwt_prefix: str
    ) -> None:
        token = auth_service.create_access_token_for_user(user=test_user, secret_key=str(SECRET_KEY))
        res = await client.get(
            app.url_path_for("users:get-current-user"),
            headers={"Authorization": f"{jwt_prefix} {token}"},
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserUpdate:
    """Test user can update detail and password."""

    async def test_authorized_client_can_change_password_and_login(
        self,
        app: FastAPI,
        client: AsyncClient,
        authorized_client: AsyncClient,
        test_user: UserInDB,
    ) -> None:
        """Test login change password and login to get token."""
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {
            "username": test_user.email,
            "password": "mypassword",
        }
        res = await client.post(app.url_path_for("users:login-email-and-password"), data=login_data)
        assert res.status_code == status.HTTP_200_OK

        # change password
        res = await authorized_client.put(
            app.url_path_for("users:update-own-detials"),
            json=jsonable_encoder(
                {"user_update": {"password": "strings"}},
            ),
        )
        assert res.status_code == status.HTTP_200_OK

        # try login again with wrong details.
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {
            "username": test_user.email,
            "password": "mypasswordss",
        }
        res = await client.post(app.url_path_for("users:login-email-and-password"), data=login_data)
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

        # try login again with correct details.
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {
            "username": test_user.email,
            "password": "strings",
        }
        res = await client.post(app.url_path_for("users:login-email-and-password"), data=login_data)
        assert res.status_code == status.HTTP_200_OK

    async def test_client_updates_email_and_username(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: UserInDB,
    ) -> None:
        """Test client can updated username and password."""
        assert test_user.email != "kent@superman.com"
        assert test_user.username != "petermain"
        res = await authorized_client.put(
            app.url_path_for("users:update-own-detials"),
            json={"user_update": {"email": "kent@superman.com", "username": "petermain"}},
        )
        assert res.status_code == status.HTTP_200_OK
        user = UserPublic(**res.json())
        assert user.email == "kent@superman.com"
        assert user.username == "petermain"
        assert user.email_verified is False
