from fastapi import APIRouter, Query

from controllers.company_controller import CompanyController
from utils.app_error import AppError

router = APIRouter()


@router.post("/import")
def import_companies() -> dict:
    try:
        count = CompanyController.import_from_csv()
    except FileNotFoundError as exc:
        raise AppError(str(exc), 404) from exc
    return {"message": "Companies imported from CSV", "count": count}


@router.get("")
def list_companies(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    slug: str | None = None,
    has_career_url: bool | None = None,
) -> dict:
    return CompanyController.list_companies(
        limit=limit,
        skip=skip,
        slug=slug,
        has_career_url=has_career_url,
    )


@router.get("/{slug}")
def get_company(slug: str) -> dict:
    company = CompanyController.get_by_slug(slug)
    if not company:
        raise AppError(f"Company not found: {slug}", 404)
    return company
