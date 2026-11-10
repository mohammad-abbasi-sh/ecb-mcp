"""MCP server: unofficial read-only access to European Central Bank
data via the official ECB SDMX API. No key, no login. NOTE: the ECB
API 504s intermittently — http.py retries 429/5xx once. Key ECB
interest rates are DAILY series (monthly keys 404)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for European Central Bank data via \
the official ECB SDMX API (no key, no login): daily euro reference \
exchange rates, key ECB interest rates (main refinancing, deposit \
facility, marginal lending), HICP inflation for the euro area and \
Germany, euro-area money supply (M1/M2/M3) and AAA-rated euro-area \
government bond yields by maturity. The ECB API 504s intermittently \
— requests are retried once. Built by Mohammad Abbasi \
(mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir \
— Germany MCP factory.\
"""

_SOURCE = "data-api.ecb.europa.eu"
_DISCLAIMER = "Unofficial read-only data from the ECB SDMX API; verify on the ECB site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("ecb-mcp", instructions=INSTRUCTIONS)


@mcp.tool()
def ecb_exchange_rates(currencies: list[str] | None = None,
                       limit: int = 5) -> str:
    """Daily euro reference exchange rates (ECB). currencies: ISO
    codes like ["USD", "GBP", "JPY"] — default: all major currencies
    (25). limit: 1..30 days of history per currency (default 5).
    Returns the latest rate per currency plus history."""
    try:
        lim = _dom.validate_limit(limit)
        codes = _dom.validate_currencies(currencies)
        rates = []
        for code in codes:
            series = _dom.parse_sdmx(
                _http.fetch_text(_dom.exchange_rate_url(code, lim)))
            latest = _dom.latest_observation(series)
            if latest is None:
                continue
            rates.append({
                "currency": code,
                "pair": f"EUR/{code}",
                "rate": latest["value"],
                "date": latest["period"],
                "history": series[0]["observations"],
            })
    except (_http.EcbMcpError, ValueError) as e:
        return _err(e)
    return _ok({"total_results": len(rates), "rates": rates})


@mcp.tool()
def ecb_interest_rates() -> str:
    """Current key ECB interest rates: main refinancing operations,
    deposit facility and marginal lending facility — with the date
    each rate took effect (daily series, latest observation)."""
    try:
        rates = []
        for code, label in _dom.KEY_RATES.items():
            series = _dom.parse_sdmx(
                _http.fetch_text(_dom.key_rate_url(code, 1)))
            latest = _dom.latest_observation(series)
            if latest is None:
                continue
            rates.append({
                "code": code,
                "name": label,
                "rate_pct": latest["value"],
                "date": latest["period"],
            })
    except (_http.EcbMcpError, ValueError) as e:
        return _err(e)
    return _ok({"total_results": len(rates), "rates": rates})


@mcp.tool()
def ecb_inflation(area: str = "U2", limit: int = 6) -> str:
    """HICP annual inflation rate (%). area: "U2" (euro area,
    default) or "DE" (Germany). limit: 1..24 months (default 6)."""
    try:
        ar = _dom.validate_area(area)
        lim = _dom.validate_limit(limit, 24)
        series = _dom.parse_sdmx(
            _http.fetch_text(_dom.inflation_url(ar, lim)))
        obs = series[0]["observations"] if series else []
    except (_http.EcbMcpError, ValueError) as e:
        return _err(e)
    return _ok({"area": ar, "area_name": _dom.INFLATION_AREAS[ar],
                "unit": "annual rate of change, %",
                "total_results": len(obs),
                "observations": obs,
                "latest": obs[-1] if obs else None})


@mcp.tool()
def ecb_money_supply(aggregate: str = "M3", limit: int = 6) -> str:
    """Euro-area money supply outstanding amounts (EUR millions).
    aggregate: "M1", "M2" or "M3" (default). limit: 1..24 months
    (default 6)."""
    try:
        agg = _dom.validate_aggregate(aggregate)
        lim = _dom.validate_limit(limit, 24)
        series = _dom.parse_sdmx(
            _http.fetch_text(_dom.money_supply_url(agg, lim)))
        obs = series[0]["observations"] if series else []
    except (_http.EcbMcpError, ValueError) as e:
        return _err(e)
    return _ok({"aggregate": agg, "unit": "EUR millions, outstanding amounts",
                "total_results": len(obs),
                "observations": obs,
                "latest": obs[-1] if obs else None})


@mcp.tool()
def ecb_bond_yields(maturity: str = "10Y", limit: int = 5) -> str:
    """AAA-rated euro-area government bond spot yields (%).
    maturity: 1Y, 2Y, 5Y, 10Y (default), 20Y or 30Y.
    limit: 1..30 days (default 5)."""
    try:
        mat = _dom.validate_maturity(maturity)
        lim = _dom.validate_limit(limit)
        series = _dom.parse_sdmx(
            _http.fetch_text(_dom.bond_yield_url(mat, lim)))
        obs = series[0]["observations"] if series else []
    except (_http.EcbMcpError, ValueError) as e:
        return _err(e)
    return _ok({"maturity": mat, "unit": "spot yield, % per annum",
                "total_results": len(obs),
                "observations": obs,
                "latest": obs[-1] if obs else None})


@mcp.tool()
def ecb_health() -> str:
    """Check whether the ECB SDMX API is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
