from fastapi import APIRouter

from routes.company_routes import router as company_router
from routes.health_routes import router as health_router
from routes.ingestion_routes import router as ingestion_router
from routes.job_routes import router as job_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(company_router, prefix="/companies", tags=["companies"])
api_router.include_router(job_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(ingestion_router, prefix="/ingestion", tags=["ingestion"])
