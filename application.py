from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from configs.db.mongo_conn import init_db
from middleware.error_handler import register_exception_handlers
from routes.router_mapping import api_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Job Jarvios API",
        description="Personal AI career assistant — job discovery and ingestion API",
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

    app.include_router(api_router, prefix="/api")

    @app.get("/test")
    def test() -> dict:
        return {"message": "Job Jarvios API is running..."}

    register_exception_handlers(app)
    return app


app = create_app()
