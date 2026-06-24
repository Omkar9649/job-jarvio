"""
Fetch jobs using scrape_type + scrape_config from the companies MongoDB document.

Supported scrape_type values: workday, rss, html_cards
"""

import re
import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from configs.settings import REQUEST_HEADERS, REQUEST_TIMEOUT

MAX_JOBS = 200
PAGE_SIZE = 20

CTA_TITLES = frozenset(
    {"apply/shortlist", "apply", "apply now", "shortlist", "view details", "learn more"}
)


def has_platform_config(company: dict) -> bool:
    return bool(company.get("scrape_type"))


def _job(title: str, url: str, location: str | None, source: str) -> dict:
    return {
        "title": title,
        "url": url.split("#")[0].rstrip("/"),
        "location": location,
        "description": None,
        "source": source,
    }


def _build_config(company: dict) -> dict | None:
    scrape_type = company.get("scrape_type")
    if not scrape_type:
        return None

    config = dict(company.get("scrape_config") or {})
    config["type"] = scrape_type

    if scrape_type == "html_cards" and not config.get("base_url"):
        career_url = company.get("career_url") or ""
        if career_url:
            parsed = urlparse(career_url)
            config["base_url"] = f"{parsed.scheme}://{parsed.netloc}"

    return config


def _fetch_workday(config: dict) -> list[dict]:
    base_url = config["base_url"].rstrip("/")
    api_url = f"{base_url}/wday/cxs/{config['tenant']}/{config['site']}/jobs"
    headers = {
        **REQUEST_HEADERS,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": f"{base_url}/en-US/{config['site']}",
    }
    jobs: list[dict] = []
    offset = 0
    search = config.get("search_text", "India")

    while len(jobs) < MAX_JOBS:
        response = requests.post(
            api_url,
            json={"appliedFacets": {}, "limit": PAGE_SIZE, "offset": offset, "searchText": search},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            break
        postings = response.json().get("jobPostings") or []
        if not postings:
            break
        for row in postings:
            title = (row.get("title") or "").strip()
            path = (row.get("externalPath") or "").strip()
            if title and path:
                jobs.append(
                    _job(
                        title,
                        urljoin(f"{base_url}/", path.lstrip("/")),
                        row.get("locationsText") or row.get("location"),
                        "workday_api",
                    )
                )
        if len(postings) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return jobs


def _fetch_rss(config: dict) -> list[dict]:
    feed_url = config.get("feed_url")
    if not feed_url:
        return []

    response = requests.get(
        feed_url,
        headers={**REQUEST_HEADERS, "Referer": feed_url},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        return []

    root = ET.fromstring(response.text)
    url_re = re.compile(config["url_pattern"], re.I) if config.get("url_pattern") else None
    jobs: list[dict] = []
    seen: set[str] = set()

    if config.get("format") == "job_xml" or "<job>" in response.text.lower():
        for job_el in root.iter("job"):
            url_el, title_el = job_el.find("url"), job_el.find("title")
            if url_el is None or not url_el.text:
                continue
            url = url_el.text.strip().rstrip("/")
            if url_re and not url_re.search(url):
                continue
            if url in seen:
                continue
            title = (title_el.text or "").strip() if title_el is not None else ""
            if not title:
                continue
            loc = ", ".join(
                p for p in [job_el.findtext("city"), job_el.findtext("state"), job_el.findtext("country")] if p
            ) or None
            seen.add(url)
            jobs.append(_job(title, url, loc, "rss_feed"))
            if len(jobs) >= MAX_JOBS:
                break
        return jobs

    for item in root.iter("item"):
        link_el, title_el = item.find("link"), item.find("title")
        if link_el is None or not link_el.text:
            continue
        url = link_el.text.strip().rstrip("/")
        if url_re and not url_re.search(url):
            continue
        if url in seen:
            continue
        title = (title_el.text or "").strip() if title_el is not None else ""
        if not title:
            continue
        seen.add(url)
        jobs.append(_job(title, url, None, "rss_feed"))
        if len(jobs) >= MAX_JOBS:
            break
    return jobs


def _parse_card_title(text: str) -> tuple[str | None, str | None]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"\s*Apply/Shortlist.*$", "", cleaned, flags=re.I)
    loc_match = re.search(r"Location\s*:\s*(.+)$", cleaned, re.I)
    location = loc_match.group(1).strip() if loc_match else None
    before_loc = re.split(r"\s+Location\s*:", cleaned, maxsplit=1, flags=re.I)[0]
    title = re.split(r"\s+Skills?(?:\s+Set)?\s*:", before_loc, maxsplit=1, flags=re.I)[0]
    title = re.sub(r"^(?:IT|BPS)\s+", "", title, flags=re.I).strip(" -|,")
    if not title or title.lower() in CTA_TITLES:
        return None, location
    return title, location


def _fetch_html_cards(config: dict) -> list[dict]:
    base_url = config.get("base_url", "").rstrip("/")
    if not base_url:
        return []

    link_contains = config.get("link_contains", "")
    parent_class = config.get("title_parent_class")
    dedupe_param = config.get("dedupe_param")
    seen: set[str] = set()
    jobs: list[dict] = []

    for path in config.get("listing_paths") or ["/"]:
        try:
            response = requests.get(
                f"{base_url}{path}",
                headers={**REQUEST_HEADERS, "Referer": base_url},
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            for anchor in soup.select(f'a[href*="{link_contains}"]'):
                href = anchor.get("href", "").strip()
                if not href:
                    continue
                url = urljoin(f"{base_url}/", href).split("#")[0]
                parent = anchor.find_parent(class_=parent_class) if parent_class else anchor.parent
                if not parent:
                    continue
                title, location = _parse_card_title(parent.get_text(" ", strip=True))
                if not title:
                    continue
                key = url
                if dedupe_param:
                    vals = parse_qs(urlparse(url).query).get(dedupe_param)
                    key = vals[0] if vals else url
                if key in seen:
                    continue
                seen.add(key)
                jobs.append(_job(title, url, location, "html_cards"))
                if len(jobs) >= MAX_JOBS:
                    return jobs
        except Exception:
            continue
    return jobs


FETCHERS = {
    "workday": _fetch_workday,
    "rss": _fetch_rss,
    "html_cards": _fetch_html_cards,
}


def fetch_jobs_via_ats(company: dict) -> list[dict]:
    config = _build_config(company)
    if not config:
        return []

    fetcher = FETCHERS.get(config.get("type"))
    if not fetcher:
        print(f"[platform] {company.get('name')}: unknown scrape_type '{config.get('type')}'")
        return []

    try:
        jobs = fetcher(config)
        if jobs:
            print(f"[{config['type']}] {company.get('name')}: {len(jobs)} jobs")
        return jobs
    except Exception as exc:
        print(f"[platform] {company.get('name')}: {exc}")
        return []
