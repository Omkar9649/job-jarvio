"""
FastAPI app — like app.js in Express.

Flow: server.py → this file → routes/ → controllers/ → models/ → MongoDB
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from configs.db.mongo_conn import init_db
from middleware.error_handler import register_exception_handlers
from routes.router_mapping import api_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Runs once when server starts (like DB connect in server.js)
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Job Jarvios API",
        description="Phase 1: job scraping API. Later: n8n + AI matching.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount all /api/* routes (like app.use('/api', routerMapping))
    app.include_router(api_router, prefix="/api")

    @app.get("/test")
    def test() -> dict:
        return {"message": "Job Jarvios API is running..."}

    register_exception_handlers(app)
    return app


app = create_app()
