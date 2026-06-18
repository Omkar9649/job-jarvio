# n8n — Daily job scrape (Phase 2)

**When to set this up:** After Phase 1 (FastAPI) works and jobs are in MongoDB.

## What this workflow does

```
Schedule (8:00 AM daily)
    → HTTP Request: POST /api/pipeline/run?limit=20
    → (optional later) HTTP Request: POST /api/match/run
    → (optional later) Send Email / Telegram
```

## Install n8n (Docker)

```bash
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
```

Open: http://localhost:5678

## Create workflow (manual steps)

1. **Schedule Trigger** — every day at 8:00 AM
2. **HTTP Request** node:
   - Method: `POST`
   - URL: `http://host.docker.internal:8000/api/pipeline/run?limit=20`
   - (On Windows Docker, use your PC IP if `host.docker.internal` fails)

3. **Save** and **Activate** workflow

## Requirements

- `python server.py` must be running (or deploy API to a server)
- MongoDB Atlas reachable from your machine

## Later nodes (Phase 3)

- Call AI match endpoint when built
- Filter jobs with score > 70
- Send digest email

Workflow JSON export will be added here when Phase 2 is implemented.
