from __future__ import annotations

import ipaddress
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

TIMEOUT_S = 10.0
MAX_BYTES = 3_000_000
USER_AGENT = "PagePulse/1.0 (+https://digitalheroesco.com; Digital Heroes training task)"


class AuditError(Exception):
    def __init__(self, code: str, http_status: int, message: str):
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.message = message


@dataclass
class FetchResult:
    final_url: str
    status_code: int
    elapsed_ms: int
    html: str


def validate_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        raise AuditError("INVALID_URL", 422, "No URL provided.")
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise AuditError("BLOCKED_SCHEME", 400,
                         "Only http:// and https:// URLs are supported.")
    if not parsed.hostname:
        raise AuditError("INVALID_URL", 422, "URL has no host.")
    _guard_ssrf(parsed.hostname)
    return raw


def _guard_ssrf(hostname: str) -> None:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # DNS failure will surface later as FETCH_FAILED during the real request
        return
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast):
            raise AuditError("BLOCKED_HOST", 400,
                             "That host resolves to a private or reserved address.")


def fetch(url: str) -> FetchResult:
    headers = {"User-Agent": USER_AGENT}
    start = time.perf_counter()
    try:
        resp = httpx.get(url, headers=headers, timeout=TIMEOUT_S,
                         follow_redirects=True)
    except httpx.TimeoutException:
        raise AuditError("TIMEOUT", 504,
                         "The page took longer than 10s to respond.")
    except httpx.RequestError:
        raise AuditError("FETCH_FAILED", 502,
                         "Could not reach that URL (DNS, connection, or TLS error).")
    elapsed_ms = round((time.perf_counter() - start) * 1000)

    ctype = resp.headers.get("content-type", "").lower()
    if "html" not in ctype:
        raise AuditError("NOT_HTML", 415,
                         f"Expected HTML but got '{ctype or 'unknown content-type'}'.")

    body = resp.content[:MAX_BYTES]
    html = body.decode(resp.encoding or "utf-8", errors="ignore")
    return FetchResult(
        final_url=str(resp.url),
        status_code=resp.status_code,
        elapsed_ms=elapsed_ms,
        html=html,
    )
