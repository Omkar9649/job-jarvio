from fastapi import APIRouter

from controllers.health_controller import HealthController

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return HealthController.check()
