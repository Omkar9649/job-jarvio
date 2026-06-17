import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from controllers.company_controller import CompanyController
from scrapers.careers.http_client import FetchError, fetch_html

OVERVIEW_URL = "https://www.ambitionbox.com/overview/{slug}-overview"
CAREER_PATHS = ("/careers", "/careers/", "/career", "/jobs", "/join-us", "/work-with-us")


def _normalize_url(url: str) -> str:
    return url.rstrip("/")


def _extract_website_from_overview(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        text = anchor.get_text(" ", strip=True).lower()
        if not href.startswith("http"):
            continue
        if "ambitionbox.com" in href:
            continue
        if any(token in text for token in ("website", "official", "visit")):
            return href

    for anchor in soup.select("a[href^='http']"):
        href = anchor.get("href", "").strip()
        if "ambitionbox.com" in href or "facebook." in href or "twitter." in href or "linkedin." in href:
            continue
        if re.search(r"\.(com|in|io|co)(/|$)", href):
            return href

    return None


def _guess_career_urls(website_url: str) -> list[str]:
    parsed = urlparse(website_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    domain = parsed.netloc.removeprefix("www.")

    guesses = [urljoin(base, path) for path in CAREER_PATHS]
    guesses.extend(
        [
            f"https://careers.{domain}",
            f"https://jobs.{domain}",
            f"https://www.{domain}/careers",
        ]
    )

    unique: list[str] = []
    seen = set()
    for url in guesses:
        normalized = _normalize_url(url)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def _looks_like_career_page(html: str, url: str) -> bool:
    lowered = html.lower()
    if len(lowered) < 500:
        return False

    signals = ("career", "job", "opening", "vacancy", "apply", "position")
    hits = sum(1 for signal in signals if signal in lowered)
    return hits >= 2 or any(signal in url.lower() for signal in signals)


def resolve_career_url(slug: str, profile_url: str | None = None) -> tuple[str | None, str, str | None]:
    known_urls = CompanyController.load_known_career_urls()
    if slug in known_urls:
        return known_urls[slug], "known", None

    website_url = None
    overview_url = OVERVIEW_URL.format(slug=slug)
    try:
        overview_html = fetch_html(overview_url, delay=False)
        website_url = _extract_website_from_overview(overview_html)
    except (FetchError, Exception):
        website_url = None

    if website_url:
        for candidate in _guess_career_urls(website_url):
            try:
                html = fetch_html(candidate)
                if _looks_like_career_page(html, candidate):
                    return candidate, "discovered", website_url
            except Exception:
                continue

    return None, "not_found", website_url


def find_career_urls(limit: int | None = 20, slug: str | None = None) -> dict[str, int]:
    companies = CompanyController.get_for_career_lookup(limit=limit, slug=slug)
    stats = {"processed": 0, "found": 0, "not_found": 0}

    for company in companies:
        stats["processed"] += 1
        career_url, status, website_url = resolve_career_url(
            company["slug"],
            company.get("profile_url"),
        )
        CompanyController.update_career_url(company["slug"], career_url, status, website_url)

        if career_url:
            stats["found"] += 1
            print(f"[found] {company['name']} -> {career_url}")
        else:
            stats["not_found"] += 1
            print(f"[miss] {company['name']} ({company['slug']})")

    return stats
