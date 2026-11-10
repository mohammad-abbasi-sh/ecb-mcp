"""Domain logic: build ECB SDMX API URLs and shape SDMX-JSON
responses into compact dicts (stdlib only).

Data source: the official ECB SDMX API
(https://data-api.ecb.europa.eu/service/data/...) — free, no key,
no login.

Datasets verified live 2026-11-10 (each key probed against the real
API; the ECB API 504s intermittently — http.py retries 429/5xx):
- EXR  D.{CUR}.EUR.SP00.A — daily euro reference rates
  (USD 1.1214 on 2026-11-10)
- FM   D.U2.EUR.4F.KR.{MRR_FR,DFR,MLFR}.LEV — key ECB rates, DAILY
  series (monthly M.* 404s; MRO 2.65%, MLFR 2.90% on 2026-11-10)
- ICP  M.{U2,DE}.N.000000.4.ANR — HICP annual rate
  (euro area 2.1%, 1.9% latest)
- BSI  M.U2.Y.V.{M10,M20,M30}.X.1.U2.2300.Z01.E — money supply
  outstanding amounts, EUR millions (M3 ~17.7 trillion)
- YC   B.U2.EUR.4F.G_N_A.SV_C_YM.SR_{2Y,5Y,10Y,20Y,30Y} — AAA-rated
  euro-area spot yield curve (10Y 3.28% on 2026-11-10)

Competitor note: scka-de/ecb-mcp (TypeScript, ★4) covers the same
API but is stale (last push 2026-03-31) — noted, proceed.
"""
from __future__ import annotations

import json

BASE = "https://data-api.ecb.europa.eu/service/data"

# Major currencies with a daily ECB euro reference rate. The API 404s
# unknown codes; validate_limit/validate_currency keep bad input out.
MAJOR_CURRENCIES = [
    "USD", "GBP", "JPY", "CHF", "SEK", "NOK", "DKK", "PLN", "CZK",
    "HUF", "AUD", "CAD", "NZD", "CNY", "KRW", "INR", "BRL", "MXN",
    "ZAR", "TRY", "ILS", "ISK", "HRK", "RON", "BGN",
]

KEY_RATES = {
    "MRR_FR": "Main refinancing operations (fixed rate)",
    "DFR": "Deposit facility",
    "MLFR": "Marginal lending facility",
}

INFLATION_AREAS = {"U2": "Euro area", "DE": "Germany"}

MONEY_AGGREGATES = {"M1": "M10", "M2": "M20", "M3": "M30"}

YIELD_MATURITIES = {"1Y", "2Y", "5Y", "10Y", "20Y", "30Y"}


def validate_limit(limit: int, maximum: int = 30) -> int:
    if not 1 <= limit <= maximum:
        raise ValueError(f"limit out of range: {limit} (expected 1..{maximum})")
    return limit


def validate_currency(code: str) -> str:
    key = (code or "").strip().upper()
    if len(key) != 3 or not key.isalpha():
        raise ValueError(f"invalid currency code: {code!r} (expected 3 letters, e.g. USD)")
    return key


def validate_currencies(codes) -> list[str]:
    if not codes:
        return list(MAJOR_CURRENCIES)
    out = []
    for c in codes:
        out.append(validate_currency(c))
    return out


def validate_area(area: str) -> str:
    key = (area or "").strip().upper()
    if key not in INFLATION_AREAS:
        raise ValueError(
            f"unsupported area: {area!r} "
            f"(use one of: {', '.join(sorted(INFLATION_AREAS))})"
        )
    return key


def validate_aggregate(aggregate: str) -> str:
    key = (aggregate or "").strip().upper()
    if key not in MONEY_AGGREGATES:
        raise ValueError(
            f"unsupported aggregate: {aggregate!r} "
            f"(use one of: {', '.join(sorted(MONEY_AGGREGATES))})"
        )
    return key


def validate_maturity(maturity: str) -> str:
    key = (maturity or "").strip().upper()
    if key not in YIELD_MATURITIES:
        raise ValueError(
            f"unsupported maturity: {maturity!r} "
            f"(use one of: {', '.join(sorted(YIELD_MATURITIES))})"
        )
    return key


def exchange_rate_url(currency: str, limit: int) -> str:
    return f"{BASE}/EXR/D.{currency}.EUR.SP00.A?lastNObservations={limit}"


def key_rate_url(code: str, limit: int) -> str:
    return f"{BASE}/FM/D.U2.EUR.4F.KR.{code}.LEV?lastNObservations={limit}"


def inflation_url(area: str, limit: int) -> str:
    return f"{BASE}/ICP/M.{area}.N.000000.4.ANR?lastNObservations={limit}"


def money_supply_url(aggregate: str, limit: int) -> str:
    suffix = MONEY_AGGREGATES[aggregate]
    return f"{BASE}/BSI/M.U2.Y.V.{suffix}.X.1.U2.2300.Z01.E?lastNObservations={limit}"


def bond_yield_url(maturity: str, limit: int) -> str:
    return (f"{BASE}/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_{maturity}"
            f"?lastNObservations={limit}")


def parse_sdmx(text: str) -> list[dict]:
    """Parse one SDMX-JSON data response into a list of series.

    Returns [{dimensions: {DIM: value, ...},
              observations: [{period, value}, ...] newest last}].
    Raises ValueError on an error payload or unparseable JSON.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid SDMX-JSON: {e}") from e
    if "dataSets" not in data:
        raise ValueError(
            "ECB API error: "
            f"{data.get('title', 'unknown')} — {data.get('detail', '')}"[:300]
        )
    structure = data.get("structure", {})
    dims = structure.get("dimensions", {})
    series_dims = dims.get("series", [])
    obs_dims = dims.get("observation", [])
    periods = [v["id"] for v in obs_dims[0]["values"]] if obs_dims else []
    out = []
    for series in data["dataSets"][0].get("series", {}).values():
        # The series key is not needed here: each call fetches one
        # series, so dimensions come from the structure's series
        # dimensions (single-value) — decode them for completeness.
        dims_out = {}
        for dim in series_dims:
            values = dim.get("values", [])
            if len(values) == 1:
                dims_out[dim["id"]] = values[0]["id"]
        obs = []
        for idx, vals in sorted(series.get("observations", {}).items(),
                                key=lambda kv: int(kv[0])):
            i = int(idx)
            period = periods[i] if i < len(periods) else str(i)
            try:
                value = float(vals[0])
            except (TypeError, ValueError, IndexError):
                continue
            obs.append({"period": period, "value": value})
        out.append({"dimensions": dims_out, "observations": obs})
    return out


def latest_observation(series: list[dict]) -> dict | None:
    """Newest observation across the (single) series, or None."""
    if not series:
        return None
    obs = series[0].get("observations", [])
    return obs[-1] if obs else None
