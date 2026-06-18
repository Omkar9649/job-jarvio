# Job Jarvios — Learning Path

You learn **3 skills** through **one project**. Do them **in order** — don't skip ahead.

```
Phase 0  →  Get data working (run.py)
Phase 1  →  Learn FastAPI (this backend)
Phase 2  →  Learn n8n (daily automation)
Phase 3  →  Build AI agent (resume matching)
```

---

## Phase 0 — Make it work (start here)

**Goal:** Companies and jobs in MongoDB. No API knowledge needed.

```bash
pip install -r requirements.txt
playwright install chromium   # once — browser for JS career sites (Workday, etc.)
python run.py setup          # once — load companies.csv
python run.py mphasis        # test JS site (Playwright)
python run.py tcs            # scrape TCS jobs
```

**Check:** MongoDB Compass → `job_jarvios` → `jobs`

**You only need to remember:** `python run.py`

---

## Phase 1 — Learn FastAPI (you are here)

**Goal:** Understand how this Python API works (same idea as Express).

### Express vs this project

| Express (your office) | Job Jarvios |
|----------------------|-------------|
| `server.js` | `server.py` |
| `app.js` | `application.py` |
| `routes/routerMapping.js` | `routes/router_mapping.py` |
| `controllers/*Controller.js` | `controllers/*_controller.py` |
| `models/*Model.js` | `models/*/*_model.py` |
| `configs/db/*.js` | `configs/db/mongo_conn.py` |
| `config.env` | `config.env` |

### Files to read (in this order)

1. **`server.py`** — starts uvicorn (like `app.listen()`)
2. **`application.py`** — creates FastAPI app, mounts `/api` routes
3. **`routes/pipeline_routes.py`** — defines `POST /run` (like a route file)
4. **`controllers/pipeline_controller.py`** — business logic (like controller)
5. **`run.py`** — same logic, but without HTTP (simpler for testing)

### One API to learn first

```bash
python server.py
```

Open: http://localhost:8000/docs

Try only these:

| API | What it does |
|-----|----------------|
| `GET /test` | Server alive? |
| `GET /api/health` | MongoDB connected? |
| `POST /api/pipeline/run?slug=tcs&limit=1` | Scrape jobs |
| `GET /api/jobs?company_slug=tcs` | Read results |

**FastAPI lesson:** Route → Controller → Model → MongoDB. Same flow as Express.

### Practice exercises

1. Change `/test` message in `application.py`, restart server, see it update
2. Call `GET /api/companies?limit=5` in Swagger
3. Run pipeline for `slug=infosys`, then `GET /api/jobs`

---

## Phase 2 — Learn n8n (after jobs are in MongoDB)

**Goal:** Automate daily job scraping without running commands manually.

### What n8n does in this project

```
Every day at 8 AM:
  n8n → POST http://localhost:8000/api/pipeline/run?limit=50
     → jobs updated in MongoDB
     → (later) trigger AI matching
```

### Why n8n?

| Without n8n | With n8n |
|-------------|----------|
| You run `python run.py` manually | Runs automatically every morning |
| Easy to forget | Cron + visual workflow |
| Hard to add email/Telegram later | Drag-and-drop nodes |

### Setup (when ready)

See `n8n/README.md` for the planned workflow.

**You only need one HTTP node** for now:
- Method: POST
- URL: `http://host.docker.internal:8000/api/pipeline/run?limit=20`

---

## Phase 3 — AI agent (later)

**Goal:** Match jobs to your resume and alert you on good fits.

```
Jobs in MongoDB
    → embed resume (Ollama)
    → vector search (Qdrant)
    → LLM ranks top matches
    → n8n sends email / Telegram
```

**Not built yet.** Finish Phase 0–2 first.

Planned folder: `agent/` (resume parser, matcher, notifier)

---

## What to ignore for now

- Multiple confusing API names — use **`/api/pipeline/run`** only
- Background job polling — API waits and returns result by default
- CSV export — MongoDB is the main storage
- Per-company scraper tuning — add URLs to `data/known_career_urls.json` as you find blockers

---

## Daily cheat sheet

| I want to… | Command |
|------------|---------|
| Scrape jobs (simple) | `python run.py` |
| Scrape one company | `python run.py tcs` |
| JS career site (Workday) | `playwright install chromium` then `python run.py mphasis` |
| Start API (learning FastAPI) | `python server.py` |
| Test API | http://localhost:8000/docs |
| See jobs | Compass or `GET /api/jobs` |

---

## Your learning order (summary)

```
Week 1:  run.py + read FastAPI files + Swagger
Week 2:  n8n calls /api/pipeline/run on schedule
Week 3+: AI agent matches resume to jobs
```

One project. Three skills. One step at a time.
