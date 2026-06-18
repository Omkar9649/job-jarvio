"""Fetch jobs from Lever public postings API."""

import requests

from configs.settings import REQUEST_HEADERS


def fetch_lever_jobs(company: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
    response.raise_for_status()

    jobs: list[dict] = []
    for item in response.json():
        title = (item.get("text") or "").strip()
        hosted_url = (item.get("hostedUrl") or "").strip()
        if not title or not hosted_url:
            continue

        location = None
        categories = item.get("categories") or {}
        if categories.get("location"):
            location = categories["location"]

        jobs.append(
            {
                "title": title,
                "url": hosted_url.split("#")[0].rstrip("/"),
                "location": location,
                "description": None,
                "source": "lever_api",
            }
        )

    return jobs
