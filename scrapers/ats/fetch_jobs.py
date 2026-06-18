"""Fetch jobs via official ATS JSON APIs (preferred over HTML scraping)."""

import json

from configs.settings import KNOWN_CAREER_URLS_PATH, ROOT_DIR
from scrapers.ats.greenhouse_api import fetch_greenhouse_jobs
from scrapers.ats.lever_api import fetch_lever_jobs
from scrapers.ats.workday_api import discover_workday_config, fetch_workday_jobs

ATS_SOURCES_PATH = ROOT_DIR / "data" / "ats_sources.json"


def _load_ats_sources() -> dict:
    if not ATS_SOURCES_PATH.exists():
        return {}
    return json.loads(ATS_SOURCES_PATH.read_text(encoding="utf-8"))


def fetch_jobs_via_ats(company: dict) -> list[dict]:
    slug = company.get("slug", "")
    career_url = company.get("career_url") or ""
    config = _load_ats_sources().get(slug)

    if not config and career_url:
        discovered = discover_workday_config(career_url)
        if discovered:
            config = discovered

    if not config:
        return []

    ats_type = config.get("type")
    try:
        if ats_type == "workday":
            jobs = fetch_workday_jobs(config)
            if jobs:
                print(f"[workday-api] {company['name']}: {len(jobs)} jobs")
            return jobs

        if ats_type == "greenhouse" and config.get("board"):
            jobs = fetch_greenhouse_jobs(config["board"])
            if jobs:
                print(f"[greenhouse-api] {company['name']}: {len(jobs)} jobs")
            return jobs

        if ats_type == "lever" and config.get("company"):
            jobs = fetch_lever_jobs(config["company"])
            if jobs:
                print(f"[lever-api] {company['name']}: {len(jobs)} jobs")
            return jobs
    except Exception as exc:
        print(f"[ats-api] {company['name']}: {exc}")

    return []
