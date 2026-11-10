"""HTTP layer for ecb_mcp — plain httpx GETs against data-api.ecb.europa.eu.

No key, no login. One retry on 429/5xx; error taxonomy (403/429/other).
"""
from __future__ import annotations

import os
import ssl
import time

import httpx

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TIMEOUT = 45.0
PROBE_URL = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=1"
SOURCE = "data-api.ecb.europa.eu"
# The ECB SDMX API serves SDMX-JSON for this media type (verified
# 2026-11-10; plain application/json is also accepted, but this is the
# documented one). The API 504s intermittently — retry covers it.
ACCEPT = "application/vnd.sdmx.data+json;version=1.0.0-wd"


class EcbMcpError(RuntimeError):
    pass


def _verify():
    """TLS trust store: the OS bundle when present, else httpx/certifi."""
    for path in (
        "/etc/ssl/certs/ca-certificates.crt",
        ssl.get_default_verify_paths().openssl_cafile,
    ):
        if path and os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return True


def _client() -> httpx.Client:
    # NOTE: we read the proxy URL from the environment but never log it.
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    return httpx.Client(
        headers={"User-Agent": UA, "Accept": ACCEPT},
        timeout=TIMEOUT,
        proxy=proxy or None,
        trust_env=False,
        verify=_verify(),
    )


def fetch_text(url: str) -> str:
    """GET one URL and return its text. One retry on 429/5xx."""
    last_exc: Exception | None = None
    r: httpx.Response | None = None
    for attempt in range(2):
        try:
            with _client() as c:
                r = c.get(url)
        except httpx.HTTPError as e:
            last_exc = e
            if attempt == 0:
                time.sleep(1.0)
                continue
            raise EcbMcpError(f"network error fetching {url}: {e}") from e
        if r.status_code in (429, 500, 502, 503, 504):
            if attempt == 0:
                time.sleep(1.0)
                continue
        break
    assert r is not None  # loop always assigns r or raises
    if r.status_code == 403:
        raise EcbMcpError(
            f"{SOURCE} returned HTTP 403 for {url} (bot wall) — try again later"
        )
    if r.status_code == 429:
        raise EcbMcpError(
            f"{SOURCE} rate-limited the request (HTTP 429) — try again later"
        )
    if r.status_code != 200:
        raise EcbMcpError(f"{SOURCE} returned HTTP {r.status_code} for {url}")
    return r.text


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `<prefix>_health` tool
    and the daily smoke CI.
    """
    url = PROBE_URL
    try:
        fetch_text(url)
    except EcbMcpError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
