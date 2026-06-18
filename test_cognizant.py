"""Temporary probe for Cognizant careers API."""
import re
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://careers.cognizant.com/global-en/jobs",
}

api_url = "https://careers.cognizant.com/wday/cxs/cognizant/Cognizant_Careers/jobs"
payload = {"appliedFacets": {}, "limit": 5, "offset": 0, "searchText": ""}
r = requests.post(api_url, json=payload, headers=headers, timeout=30)
print("Workday API status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    postings = data.get("jobPostings", [])
    print("Jobs count:", len(postings))
    for p in postings[:3]:
        print(" -", p.get("title"), "|", p.get("externalPath"))
else:
    print("Response:", r.text[:500])

print()
r2 = requests.get("https://careers.cognizant.com/global-en", headers={"User-Agent": headers["User-Agent"]}, timeout=30)
print("Homepage status:", r2.status_code)
m = re.search(r"wday/cxs/([^/\"'\s]+)/([^/\"'\s]+)/jobs", r2.text)
print("Workday path in HTML:", m.group(0) if m else "NOT FOUND")

# Try jobs listing page
r3 = requests.get("https://careers.cognizant.com/global-en/jobs", headers={"User-Agent": headers["User-Agent"]}, timeout=30)
print("Jobs page status:", r3.status_code)
soup = BeautifulSoup(r3.text, "html.parser")
print("Links with /jobs/ on jobs page:")
for a in soup.select("a[href*='jobs']")[:10]:
    print(" ", repr(a.get_text(strip=True)[:50]), "->", (a.get("href") or "")[:100])

# Try alternate API paths
for path in [
    "https://careers.cognizant.com/global-en/wday/cxs/cognizant/Cognizant_Careers/jobs",
    "https://careers.cognizant.com/api/jobs",
]:
    try:
        rr = requests.post(path, json=payload, headers=headers, timeout=15)
        print(f"\n{path} -> {rr.status_code}")
        if rr.status_code == 200:
            print(rr.text[:300])
    except Exception as e:
        print(f"\n{path} -> error: {e}")
