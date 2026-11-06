"""ClearPath FastAPI Backend.
Serves REST API, initiates background pipeline analyses via subprocesses,
and streams video files with HTTP Range 206 support.
"""
import ipaddress
import os
import re
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from worker.common import DATA_DIR, now_iso, read_json, write_json
from api.export import generate_html_report

app = FastAPI(title="ClearPath API", version="1.0.0")

# CORS setup for local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_HOSTS = [h.strip().lower() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testsite").split(",")]

# Generated ids are uuid4 hex; pre-baked demo runs use names like "bad-checkout".
ANALYSIS_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,64}")


def analysis_dir(analysis_id: str) -> Path:
    """Resolves data/{id}, rejecting ids that could escape DATA_DIR (e.g. '..')."""
    if not ANALYSIS_ID_PATTERN.fullmatch(analysis_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
    return DATA_DIR / analysis_id


class AnalysisRequest(BaseModel):
    url: str
    lang: Literal["ro", "en"] = "ro"


def validate_target_url(url: str) -> None:
    """Validates URL format, prevents SSRF against private networks (unless whitelisted), and tests reachability."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL-ul trebuie să înceapă cu http:// sau https://",
        )

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL-ul nu conține un nume de host valid.",
        )

    # Check allowed local hosts
    if hostname not in ALLOWED_HOSTS:
        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Host-urile din rețeaua privată nu sunt permise.",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Host-ul specificat nu a putut fi rezolvat prin DNS.",
            )

    # Reachability test
    try:
        resp = httpx.get(url, timeout=10.0, follow_redirects=True)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Pagina nu poate fi accesată (status HTTP {resp.status_code}).",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pagina nu poate fi accesată. Verificați că serverul țintă este pornit.",
        )


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/analyses", status_code=status.HTTP_202_ACCEPTED)
def create_analysis(req: AnalysisRequest):
    target_url = req.url.strip()
    validate_target_url(target_url)

    analysis_id = uuid4().hex[:8]
    job_dir = DATA_DIR / analysis_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Write initial queued status
    status_obj = {
        "id": analysis_id,
        "url": target_url,
        "status": "queued",
        "lang": req.lang,
        "error": None,
        "updated_at": now_iso(),
    }
    write_json(job_dir / "status.json", status_obj)

    # Launch pipeline as an independent background subprocess
    log_file = open(job_dir / "pipeline.log", "w", encoding="utf-8")
    subprocess.Popen(
        [sys.executable, "-m", "worker.pipeline", analysis_id, target_url, "--lang", req.lang],
        cwd=ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    return {"id": analysis_id, "lang": req.lang}


@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    job_dir = analysis_dir(analysis_id)
    status_path = job_dir / "status.json"
    if not status_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analiza nu a fost găsită.")

    status_data = read_json(status_path)
    report_data = None
    if status_data.get("status") == "done":
        report_path = job_dir / "report.json"
        if report_path.exists():
            report_data = read_json(report_path)

    return {
        "id": status_data.get("id", analysis_id),
        "url": status_data.get("url"),
        "status": status_data.get("status"),
        "lang": status_data.get("lang", "ro"),
        "error": status_data.get("error"),
        "report": report_data,
    }


@app.get("/api/analyses/{analysis_id}/timeline")
def get_timeline(analysis_id: str):
    """Returns the finished analysis's timeline.json (narration entries with timestamps)."""
    job_dir = analysis_dir(analysis_id)
    status_path = job_dir / "status.json"
    if not status_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
    if read_json(status_path).get("status") != "done":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Analysis is not finished yet.")
    timeline_path = job_dir / "timeline.json"
    if not timeline_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Timeline not found for this analysis.")
    return read_json(timeline_path)


@app.get("/api/analyses/{analysis_id}/export")
def export_analysis(analysis_id: str, format: Literal["html", "json"] = "html"):
    """Download finished analysis evidence; HTML can be printed to PDF."""
    job_dir = analysis_dir(analysis_id)
    status_path = job_dir / "status.json"
    if not status_path.is_file():
        raise HTTPException(status_code=404, detail="Analysis not found.")
    state = read_json(status_path)
    if state.get("status") != "done":
        raise HTTPException(status_code=409, detail="Analysis is not finished yet.")
    report_path = job_dir / "report.json"
    if not report_path.is_file():
        raise HTTPException(status_code=404, detail="Report not found.")
    headers = {
        "Content-Disposition": f'attachment; filename="clearpath-audit-{analysis_id}.{format}"',
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'",
    }
    if format == "json":
        return Response(report_path.read_bytes(), media_type="application/json", headers=headers)
    def optional(name):
        path = job_dir / name
        return read_json(path) if path.is_file() else None
    content = generate_html_report(
        read_json(report_path), timeline=optional("timeline.json"), nodes=optional("nodes.json"),
        metadata={"completed_at": state.get("updated_at")},
    )
    return Response(content, media_type="text/html", headers=headers)


@app.get("/media/{analysis_id}/clip.mp4")
def stream_clip(analysis_id: str, request: Request):
    """Streams the analysis video with explicit HTTP Range 206 Partial Content support."""
    video_path = analysis_dir(analysis_id) / "clip.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clipul video nu există.")

    file_size = video_path.stat().st_size
    range_header = request.headers.get("Range")

    if not range_header:
        # Full content response
        with open(video_path, "rb") as f:
            content = f.read()
        return Response(
            content=content,
            status_code=status.HTTP_200_OK,
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
            },
        )

    # Partial range response (HTTP 206)
    try:
        range_value = range_header.replace("bytes=", "").strip()
        parts = range_value.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
        end = min(end, file_size - 1)
        length = end - start + 1

        with open(video_path, "rb") as f:
            f.seek(start)
            data = f.read(length)

        return Response(
            content=data,
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(length),
                "Accept-Ranges": "bytes",
            },
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail="Interval Range invalid.")
