"""API routes."""

from app.api.routes.comments import router as comment_router
from app.api.routes.evaluations import router as evaluations_router
from app.api.routes.feed import router as feed_router
from app.api.routes.profiles import router as profile_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.todos import router as todos_router
from app.api.routes.users import router as users_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(todos_router, prefix="/todos", tags=["todos"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(profile_router, prefix="/profiles", tags=["profiles"])
router.include_router(comment_router, prefix="/comments", tags=["comments"])
router.include_router(tasks_router, prefix="/todos/{todo_id}/tasks", tags=["tasks"])
router.include_router(evaluations_router, prefix="/users/{username}/evaluations", tags=["evaluations"])
router.include_router(feed_router, prefix="/feed", tags=["feed"])
