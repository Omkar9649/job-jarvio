from fastapi import APIRouter

from routes.company_routes import router as company_router
from routes.health_routes import router as health_router
from routes.job_routes import router as job_router
from routes.pipeline_routes import router as pipeline_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
# Old URL still works (same as /pipeline)
api_router.include_router(pipeline_router, prefix="/ingestion", tags=["pipeline"])
api_router.include_router(company_router, prefix="/companies", tags=["companies"])
api_router.include_router(job_router, prefix="/jobs", tags=["jobs"])
