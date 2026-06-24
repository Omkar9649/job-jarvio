# Job Jarvios

**Personal AI career assistant** — finds jobs from company career pages and (later) matches them to your resume.

---

## Branding

| Context | Name |
|---------|------|
| **Product / display name** | Job Jarvios |
| **GitHub repo / folder** | `job-jarvios` |
| **Python package** | `job_jarvios` |
| **Database file** | `job_jarvios` (MongoDB) |
| **Tagline** | Personal AI career assistant |

Inspired by the idea of a personal assistant (J.A.R.V.I.S.) — built to help you find the right job, not just more jobs.
---

## Problem

Manual job hunting on Naukri, LinkedIn, and company career pages is slow and noisy. Most listings are irrelevant to your skills and experience. This project automates discovery and ranking so you apply to fewer, better-fit roles.

---

## Solution

```
Collect all jobs  →  Store in database  →  Match against resume  →  Alert top matches only
```

| Layer | Responsibility |
|-------|----------------|
| **Scrapers** | Collect companies and job postings (no filtering) |
| **Database** | Store companies, jobs, matches, and history |
| **AI / RAG** | Embed resume + jobs, vector similarity, LLM rerank |
| **Automation** | n8n daily cron pipeline |
| **Notifications** | Email / Telegram digest |

---

## Tech Stack

| Component | Tool | Cost |
|-----------|------|------|
| Language | Python 3.11+ | Free |
| API | FastAPI + uvicorn | Free |
| Scraping | requests, BeautifulSoup, Playwright (JS sites) | Free |
| LLM | Ollama (llama3.2) | Free |
| Embeddings | Ollama (nomic-embed-text) | Free |
| Vector DB | Qdrant | Free (Docker) |
| Database | MongoDB (local) + pymongo | Free |
| Automation | n8n (self-hosted) | Free |
| Notifications | Gmail SMTP / Telegram Bot | Free |
| MCP (later) | Python MCP SDK | Free |

---

## Current Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0 — Setup | **Done** | FastAPI + Express-style layout |
| Phase 1 — Company list | **Done** | ~5,700 companies in `companies.csv` |
| Phase 1 — Job scraping | **In progress** | Career URL finder + job scraper added |
| Phase 2 — Resume + vectors | Not started | — |
| Phase 3 — RAG matching | Not started | — |
| Phase 4 — n8n automation | Not started | — |
| Phase 5 — Notifications | Not started | — |

---

## Project Structure

### Current layout (Express-style + FastAPI)

```
job-jarvio/
├── server.py                             # entry point (like server.js)
├── application.py                        # FastAPI app (like app.js)
├── config.env
├── config.env.example
├── requirements.txt
├── companies.csv
│
├── configs/
│   ├── settings.py                       # env + app constants
│   └── db/
│       ├── mongo_conn.py                 # like configs/db/conveyance.js
│       └── collections.py                # like configs/db/tables.js
│
├── routes/
│   ├── router_mapping.py                 # like routes/routerMapping.js
│   ├── health_routes.py
│   ├── company_routes.py
│   ├── job_routes.py
│   ├── pipeline_routes.py
│
├── controllers/
│   ├── health_controller.py
│   ├── company_controller.py
│   ├── job_controller.py
│   └── pipeline_controller.py
│
├── models/
│   ├── companies/
│   │   └── company_model.py              # like Sequelize define()
│   └── jobs/
│       └── job_model.py
│
├── middleware/
│   └── error_handler.py                  # like middleware/error.js
│
├── utils/
│   └── app_error.py                      # like utils/appError.js
│
├── data/
│   └── exports/jobs.csv                  # generated on scrape
│
├── scrapers/
│   └── careers/
│       ├── find_career_urls.py
│       ├── scrape_jobs.py
│       ├── fetch_jobs.py
│       ├── job_parser.py
│       ├── playwright_scraper.py
│       └── http_client.py
│
└── run.py                                # simple CLI (use this daily)
```

### Target layout (later phases)

```
job-jarvio/
├── services/                             # resume, embed, match, notify (Phase 3+)
└── validations/
```

---

## How It Works

### End-to-end pipeline

```mermaid
flowchart LR
    A[AmbitionBox company list] --> B[Career page scraper]
    B --> C[(MongoDB - all jobs)]
    D[Your resume] --> E[Chunk + embed]
    E --> F[(Qdrant vector DB)]
    C --> G[Embed new jobs]
    G --> F
    F --> H[Vector similarity - top 20]
    H --> I[Ollama LLM rerank]
    I --> J[Top 5-10 matches]
    J --> K[Email / Telegram]
```

### Why save all jobs (not only relevant ones)?

The database stores **every** scraped job. Intelligence runs in a separate matching step:

1. **SQL filters** — location, experience band, role keywords (fast, cheap)
2. **Vector search** — resume embeddings vs job embeddings (semantic match)
3. **LLM rerank** — Ollama scores top candidates and explains fit

Irrelevant jobs stay in the DB but are never sent in alerts.

### Daily flow (n8n cron, 8:00 AM)

```
1. Scrape career pages for target companies
2. Insert new jobs into database (dedupe by URL)
3. Embed only new jobs → Qdrant
4. Vector search: resume vs recent jobs → top 20
5. Ollama rerank → top 5-10 with match score + reason
6. Send digest if score > 70
```

---

## Phases

### Phase 0 — Environment setup (Week 0)

- [x] Python scraper for AmbitionBox companies
- [ ] Reorganize into target folder structure
- [ ] Docker Compose: n8n, Ollama, Qdrant
- [ ] Pull Ollama models: `llama3.2`, `nomic-embed-text`
- [ ] `config.env` for MongoDB Atlas credentials

### Phase 1 — Data collection (Week 1)

- [x] Scrape filtered company list from AmbitionBox (~5,700 companies)
- [x] MongoDB collections: `companies`, `jobs`
- [ ] Career page URL finder (start with top 20–50 companies)
- [ ] Career page job scraper (title, location, description, apply URL)
- [ ] Job deduplication by URL

**Done when:** 50+ real jobs from 10–20 companies stored in database.

### Phase 2 — Resume + vector search (Week 2)

- [ ] Resume input (PDF or plain text)
- [ ] Chunk resume: skills, experience, projects, education
- [ ] Generate embeddings via Ollama
- [ ] Qdrant collections: `resume_chunks`, `jobs`
- [ ] Basic similarity search: top 20 jobs per run

**Done when:** Running match returns ranked jobs based on resume.

### Phase 3 — RAG + LLM ranking (Week 3)

- [ ] Ollama prompt: score jobs 0–100, explain fit, list missing skills
- [ ] Filter: only jobs with score > 70
- [ ] Store match history in `matches` table

**Done when:** LLM returns explained, ranked top 5–10 jobs.

### Phase 4 — Automation (Week 3–4)

- [x] `run.py` — full pipeline in one command
- [ ] n8n workflow: daily cron → scrape → match → notify
- [ ] Error handling and logging

**Done when:** Pipeline runs daily without manual intervention.

### Phase 5 — Notifications (Week 4)

- [ ] Email digest (Gmail SMTP)
- [ ] Telegram bot alerts (optional, free alternative to WhatsApp)

**Done when:** You receive a daily list of relevant jobs.

### Phase 6 — Portfolio (Week 4)

- [ ] README with architecture diagram
- [ ] Demo video (2–3 minutes)
- [ ] Resume / LinkedIn project bullets
- [ ] Public GitHub repo

### Phase 7 — Enhancements (Later)

- [ ] Ingest Naukri / LinkedIn job alert emails via IMAP
- [x] FastAPI REST API (pipeline + read endpoints)
- [ ] Resume + match endpoints (`GET /matches/today`, `POST /resume`)
- [ ] MCP server for chat-based job search
- [ ] Simple web dashboard (view matches, mark applied)

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker Desktop (for n8n, Ollama, Qdrant — later phases)

### Install Python dependencies

```bash
cd job-jarvio
pip install -r requirements.txt
```

### Step 1 — Import companies (first time only)

```bash
python run.py setup
```

### Start the API

```bash
cd job-jarvio
pip install -r requirements.txt
python server.py
```

Swagger: `http://localhost:8000/docs`

### API design (simple — one automation endpoint)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| **POST** | **`/api/pipeline/run`** | **Main automation** — career URLs + scrape jobs + export CSV |
| GET | `/api/pipeline/status` | Check pipeline progress |
| GET | `/api/companies` | List companies (read) |
| GET | `/api/companies/{slug}` | One company (read) |
| GET | `/api/jobs` | List scraped jobs (read) |
| GET | `/api/health` | Health check |

### First time (import companies from CSV)

```bash
curl -X POST "http://localhost:8000/api/pipeline/run?import_companies=true&limit=1"
```

### Daily automation (companies already in MongoDB)

```bash
curl -X POST "http://localhost:8000/api/pipeline/run?limit=10"
```

### One company (e.g. TCS)

```bash
curl -X POST "http://localhost:8000/api/pipeline/run?slug=tcs&limit=1"
```

### Check status + results

```bash
curl http://localhost:8000/api/pipeline/status
curl "http://localhost:8000/api/jobs?company_slug=tcs&limit=10"
```

### CLI (simplest)

```bash
python run.py setup
python run.py tcs
python run.py --limit 10
```

Output:
- MongoDB database: `job_jarvios`
- Jobs export: `data/exports/jobs.csv`

Flow:
1. Import `companies.csv` → MongoDB `companies` collection
2. Resolve **official career URLs** (MongoDB `career_url` + discovery)
3. Scrape job links from career pages → `jobs` collection
4. Export all jobs to CSV

---

## MongoDB collections

**companies:** name, slug, rating, profile_url, website_url, career_url, career_url_status, last_scraped_at

**jobs:** company_id, company_slug, company_name, title, location, description, url, source, scraped_at

**Later:** resume_chunks, matches (Phase 3+)

---

## Configuration (`config.env`)

Copy `config.env.example` → `config.env` and add your Atlas connection string:

```env
MONGO_URI=mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=job_jarvios
PORT=8000
```

---

## Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Primary language | Python | Best for scraping, RAG, MCP |
| API framework | FastAPI | Closest to Express for JSON APIs |
| Start with framework? | No — scripts first | Simpler for personal single-user use |
| Save all jobs? | Yes | Filter at match time, not scrape time |
| LLM | Ollama local | Free, private resume data |
| Job sources (v1) | Company career pages | More reliable than scraping Naukri/LinkedIn |
| Scale | Personal use only | Architecture allows growth later |

---

## Portfolio Value

This project demonstrates:

- Web scraping and data ingestion
- Database design and ETL pipelines
- Vector embeddings and semantic search
- RAG (Retrieval Augmented Generation)
- Local LLM integration (Ollama)
- Workflow automation (n8n)
- System design: collect → index → match → notify

---

## License

Personal project. Not for commercial redistribution of scraped data.

---

## Author

Omkar — [Job Jarvios](https://github.com/yourusername/job-jarvios): personal AI career assistant.
