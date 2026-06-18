"""Fetch jobs from Workday Candidate Experience Service (CXS) — no browser needed."""

import re
from urllib.parse import urljoin, urlparse

import requests

from configs.settings import REQUEST_HEADERS

WORKDAY_JOBS_PATH = re.compile(
    r"(https?://[^\"'\s]+)/wday/cxs/([^/\"'\s]+)/([^/\"'\s]+)/jobs",
    re.I,
)

PAGE_SIZE = 20
MAX_JOBS = 200


def _workday_headers(base_url: str, tenant: str, site: str) -> dict:
    return {
        **REQUEST_HEADERS,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": f"{base_url.rstrip('/')}/en-US/{site}",
    }


def discover_workday_config(career_url: str) -> dict | None:
    """Try to find tenant/site from career page HTML or common search URLs."""
    base = f"{urlparse(career_url).scheme}://{urlparse(career_url).netloc}"
    pages = [
        career_url,
        f"{base}/en-US/search-results",
        f"{base}/search-results",
        f"{base}/jobs",
    ]

    for page_url in pages:
        try:
            response = requests.get(page_url, headers=REQUEST_HEADERS, timeout=30)
            if response.status_code != 200:
                continue
            match = WORKDAY_JOBS_PATH.search(response.text)
            if match:
                return {
                    "type": "workday",
                    "base_url": match.group(1).rstrip("/"),
                    "tenant": match.group(2),
                    "site": match.group(3),
                }
        except Exception:
            continue

    return None


def fetch_workday_jobs(config: dict, location_filter: str | None = "India") -> list[dict]:
    base_url = config["base_url"].rstrip("/")
    tenant = config["tenant"]
    site = config["site"]
    api_url = f"{base_url}/wday/cxs/{tenant}/{site}/jobs"

    jobs: list[dict] = []
    offset = 0

    while offset < MAX_JOBS:
        payload = {
            "appliedFacets": {},
            "limit": PAGE_SIZE,
            "offset": offset,
            "searchText": location_filter or "",
        }

        response = requests.post(
            api_url,
            json=payload,
            headers=_workday_headers(base_url, tenant, site),
            timeout=30,
        )
        if response.status_code != 200:
            break

        data = response.json()
        postings = data.get("jobPostings") or []
        if not postings:
            break

        for posting in postings:
            title = (posting.get("title") or "").strip()
            external_path = (posting.get("externalPath") or "").strip()
            if not title or not external_path:
                continue

            job_url = urljoin(f"{base_url}/", external_path.lstrip("/"))
            location = posting.get("locationsText") or posting.get("location")

            jobs.append(
                {
                    "title": title,
                    "url": job_url.split("#")[0].rstrip("/"),
                    "location": location,
                    "description": None,
                    "source": "workday_api",
                }
            )

        if len(postings) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    return jobs
