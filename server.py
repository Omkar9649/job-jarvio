"""Entry point — like server.js in Express. Starts uvicorn on PORT from config.env."""

import sys
import signal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import uvicorn

from configs.settings import PORT

def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"Starting Job Jarvios API on http://localhost:{PORT}")
    print(f"Swagger docs: http://localhost:{PORT}/docs")

    # "application:app" = load application.py and use the `app` object (like require('./app'))
    uvicorn.run(
        "application:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
    )
