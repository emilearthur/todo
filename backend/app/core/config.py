"""Settting up configs."""

from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

PROJECT_NAME = "occupy_todo"
VERSION = "0.0.1"
API_PREFIX = "/api"

SECRET_KEY = config("SECRET_KEY", cast=Secret)

ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=7 * 24 * 60)

JWT_ALGORITHM = config("JWT_ALGORITHM", cast=str, default="HS256")
JWT_AUDIENCE = config("JWT_AUDIENCE", cast=str, default="occupy_todo:auth")
JWT_TOKEN_PREFIX = config("JWT_TOKEN_PREFIX", cast=str, default="Bearer")

POSTGRES_USER = config("POSTGRES_USER", cast=str)
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD", cast=Secret)
POSTGRES_SERVER = config("POSTGRES_SERVER", cast=str, default="db")
POSTGRES_PORT = config("POSTGRES_PORT", cast=str, default="5432")
POSTGRES_DB = config("POSTGRES_DB", cast=str)

REDIS_HOST = config("REDIS_HOST", cast=str, default="redis")
REDIS_PASSWORD = config("REDIS_PASSWORD", cast=Secret)
REDIS_PORT = config("REDIS_PORT", cast=str, default="6379")

EMAIL_ADDR = config("EMAIL", cast=str)
EMAIL_PWD = config("EMAIL_PWD", cast=str)
EMAIL_USERNAME = config("EMAIL_USERNAME", cast=str, default="EMILEX TRIG")

DATABASE_URL = config(
    "DATABASE_URL",
    cast=DatabaseURL,
    default=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}",
)

REDIS_URL = config("REDIS_URL", cast=str, default=f"redis://{REDIS_HOST}")
