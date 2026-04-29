from fastapi import APIRouter

from api.auth import router as auth_router
from api.logs import router as logs_router
from api.relay import router as relay_router
from api.stats import router as stats_router
from api.system import router as system_router
from api.vehicles import router as vehicles_router
from api.webhook import router as webhook_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(logs_router)
api_router.include_router(relay_router)
api_router.include_router(stats_router)
api_router.include_router(system_router)
api_router.include_router(vehicles_router)
api_router.include_router(webhook_router)
