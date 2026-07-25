from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from app import auditor, fetcher, scoring
from app.models import AuditReport, AuditRequest, Metrics

app = FastAPI(title="Page Pulse")

STATIC_DIR = Path(__file__).parent / "static"


@app.exception_handler(fetcher.AuditError)
async def audit_error_handler(request: Request, exc: fetcher.AuditError):
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Request body is invalid — expected JSON with a 'url' string.",
            }
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while auditing the page.",
            }
        },
    )


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/audit")
def audit(req: AuditRequest) -> AuditReport:
    url = fetcher.validate_url(req.url)
    result = fetcher.fetch(url)
    parsed = auditor.parse_html(result.html)
    metrics = Metrics(
        http_status=result.status_code,
        response_time_ms=result.elapsed_ms,
        title=parsed.title,
        meta_description=parsed.meta_description,
        h1_count=parsed.h1_count,
        images_total=parsed.images_total,
        images_missing_alt=parsed.images_missing_alt,
        word_count=parsed.word_count,
    )
    card, fixes = scoring.evaluate(metrics)
    return AuditReport(
        final_url=result.final_url,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        metrics=metrics,
        score=card,
        fixes=fixes,
    )
