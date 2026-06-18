"""Fetch jobs from Greenhouse public board API."""

import requests

from configs.settings import REQUEST_HEADERS


def fetch_greenhouse_jobs(board: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
    response.raise_for_status()

    jobs: list[dict] = []
    for item in response.json().get("jobs", []):
        title = (item.get("title") or "").strip()
        absolute_url = (item.get("absolute_url") or "").strip()
        if not title or not absolute_url:
            continue

        location = None
        if item.get("location") and item["location"].get("name"):
            location = item["location"]["name"]

        jobs.append(
            {
                "title": title,
                "url": absolute_url.split("#")[0].rstrip("/"),
                "location": location,
                "description": None,
                "source": "greenhouse_api",
            }
        )

    return jobs
