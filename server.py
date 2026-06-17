"""Entry point (like server.js in Express projects)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import uvicorn

from configs.settings import PORT

if __name__ == "__main__":
    uvicorn.run(
        "application:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
    )
