# ecb-mcp 💶

mcp-name: io.github.mohammad-abbasi-sh/ecb-mcp

Unofficial **read-only** MCP server for **[data-api.ecb.europa.eu](https://data-api.ecb.europa.eu)** — European Central Bank data via the official ECB SDMX API (free, no key, no login): euro exchange rates, key ECB interest rates, HICP inflation, M3 money supply and euro-area bond yields. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory". Not affiliated with data-api.ecb.europa.eu.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "ecb": {
      "command": "uvx",
      "args": ["ecb-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m ecb_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `ecb_exchange_rates` | Daily euro reference rates — `currencies` (e.g. USD,GBP,JPY,CHF; default all majors), `limit` 1..30 days |
| `ecb_interest_rates` | Current key ECB interest rates — no params; returns MRO, deposit facility and marginal lending rates with dates |
| `ecb_inflation` | HICP annual inflation rate — `area`: U2 (euro area, default) or DE (Germany); `limit` 1..24 months |
| `ecb_money_supply` | Money supply outstanding amounts — `aggregate`: M1, M2 or M3 (default M3); `limit` 1..24 months |
| `ecb_bond_yields` | AAA-rated euro-area yield curve — `maturity`: 2Y, 5Y, 10Y (default), 20Y or 30Y; `limit` 1..30 days |
| `ecb_health` | Reachability probe (ok / blocked / error) — one polite request |

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
