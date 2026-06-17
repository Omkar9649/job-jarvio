"""
Step 1: fetch company names from AmbitionBox list pages.

Note: AmbitionBox Terms of Use prohibit automated scraping. Use only for
personal learning; do not republish data or run aggressive bulk jobs.
"""

import csv
import re
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = ROOT / "companies.csv"

BASE_URL = "https://www.ambitionbox.com/list-of-companies"
FILTERS = {
    "locations": "mumbai,pune,navi-mumbai,mumbai-suburban-maharashtra,thane",
    "industries": "it-services-and-consulting",
    "sortBy": "popular",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-IN,en;q=0.9",
}

DELAY_SECONDS = 3


def build_page_url(page: int) -> str:
    params = {**FILTERS, "page": page}
    return f"{BASE_URL}?{urlencode(params)}"


def parse_companies(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    companies = []

    for card in soup.select("div.companyCardWrapper"):
        name_el = card.select_one("h2.companyCardWrapper__companyName")
        if not name_el:
            continue

        name = name_el.get_text(strip=True)
        link_el = card.select_one("a[href*='/overview/'], a[href*='/reviews/']")
        href = link_el.get("href", "") if link_el else ""
        slug_match = re.search(r"/(?:overview|reviews)/([^/?]+)", href)
        slug = slug_match.group(1).replace("-reviews", "").replace("-overview", "") if slug_match else ""

        rating_el = card.select_one(".companyCardWrapper__companyRating .rating_text")
        rating = rating_el.get_text(strip=True) if rating_el else ""

        companies.append(
            {
                "company_name": name,
                "slug": slug,
                "rating": rating,
                "profile_url": f"https://www.ambitionbox.com{href}" if href.startswith("/") else href,
            }
        )

    return companies


def fetch_page(session: requests.Session, page: int) -> list[dict]:
    url = build_page_url(page)
    response = session.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    if "access denied" in response.text.lower():
        raise RuntimeError(f"Blocked on page {page}. Stop and retry later with higher delay.")

    return parse_companies(response.text)


def scrape_all(max_pages: int | None = None, output_csv: Path = OUTPUT_CSV) -> None:
    session = requests.Session()
    all_companies: list[dict] = []
    page = 1

    while True:
        if max_pages and page > max_pages:
            break

        print(f"Fetching page {page}...")
        batch = fetch_page(session, page)
        if not batch:
            print("No more companies found.")
            break

        all_companies.extend(batch)
        print(f"  got {len(batch)} companies (total so far: {len(all_companies)})")
        page += 1
        time.sleep(DELAY_SECONDS)

    seen = set()
    unique = []
    for row in all_companies:
        key = row["slug"] or row["company_name"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)

    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["company_name", "slug", "rating", "profile_url"])
        writer.writeheader()
        writer.writerows(unique)

    print(f"Saved {len(unique)} companies to {output_csv}")


if __name__ == "__main__":
    scrape_all()
