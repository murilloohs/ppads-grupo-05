from fastapi import APIRouter

from app.controllers.activities import router as activities_router
from app.controllers.auth import router as auth_router
from app.controllers.health_controller import router as health_router
from app.controllers.institutions_controller import router as institutions_router
from app.controllers.reviews import router as reviews_router
from app.controllers.rules import router as rules_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(institutions_router)
api_router.include_router(auth_router)
api_router.include_router(activities_router)
api_router.include_router(rules_router)
api_router.include_router(reviews_router)
