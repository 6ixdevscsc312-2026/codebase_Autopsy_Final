"""
webapp.py
Web layer for Codebase Autopsy. Serves the dashboard UI and a JSON API
that wraps the existing pipeline (ingest -> graph -> Bob analysis).

Run locally:
    uvicorn autopsy.webapp:app --reload --port 8000

Deploy: see DEPLOY.md at the repo root.

Security notes (public-facing deployment):
  - Only github.com / gitlab.com / bitbucket.org URLs can be cloned
    (autopsy/source.py ALLOWED_HOSTS) — not an open clone proxy.
  - `mock` defaults to True for POST /api/analyze. Real Bob calls cost
    Bobcoins from a shared, limited budget — real=True should stay
    something *you* trigger deliberately, not the default for random
    visitors hitting a public link.
  - DEFAULT_MAX_MODULES caps how many Bob calls one request can trigger.
"""

from __future__ import annotations

import json
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from autopsy.main import run_autopsy, run_autopsy_stream
from autopsy.source import SourceError, resolve_repo

app = FastAPI(title="Codebase Autopsy")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
DEFAULT_MAX_MODULES = 25


class AnalyzeRequest(BaseModel):
    repo: str = Field(..., description="Local path or a github.com/gitlab.com/bitbucket.org URL")
    mock: bool = True
    max_modules: int = Field(default=DEFAULT_MAX_MODULES, ge=1, le=100)


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    """Non-streaming variant — returns the full report in one response.
    Kept for programmatic/API use. The web UI uses /api/analyze/stream
    instead, for live per-module progress."""
    if not req.mock and not os.environ.get("BOB_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="Server has no BOB_API_KEY configured — only mock=true requests are available.",
        )
    try:
        with resolve_repo(req.repo) as local_path:
            report = run_autopsy(local_path, mock=req.mock, max_modules=req.max_modules)
    except SourceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}") from e
    return JSONResponse(report)


@app.get("/api/analyze/stream")
def analyze_stream(
    repo: str = Query(...),
    mock: bool = Query(True),
    max_modules: int = Query(DEFAULT_MAX_MODULES, ge=1, le=100),
):
    """Server-Sent Events endpoint: emits {"type":"scan"|"progress"|"error"|"done", ...}
    events as the analysis runs, so the UI can show real per-module progress
    instead of a blank spinner. GET + query params (rather than POST) so the
    browser's native EventSource can be used on the frontend."""
    if not mock and not os.environ.get("BOB_API_KEY"):
        def err_gen():
            yield _sse({"type": "error", "detail": "Server has no BOB_API_KEY configured."})
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    def event_gen():
        try:
            with resolve_repo(repo) as local_path:
                for event in run_autopsy_stream(local_path, mock=mock, max_modules=max_modules):
                    yield _sse(event)
        except SourceError as e:
            yield _sse({"type": "error", "detail": str(e)})
        except Exception as e:  # noqa: BLE001
            yield _sse({"type": "error", "detail": f"Analysis failed: {e}"})

    return StreamingResponse(event_gen(), media_type="text/event-stream")


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "bob_configured": bool(os.environ.get("BOB_API_KEY")),
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
