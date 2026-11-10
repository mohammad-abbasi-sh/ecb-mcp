# ecb-mcp 💶

mcp-name: io.github.mohammad-abbasi-sh/ecb-mcp

Inoffizieller **nur lesender** MCP-Server für **[data-api.ecb.europa.eu](https://data-api.ecb.europa.eu)** — Daten der Europäischen Zentralbank über die offizielle EZB-SDMX-API (kostenlos, kein Schlüssel, kein Login): Euro-Wechselkurse, EZB-Leitzinsen, HVPI-Inflation, Geldmenge M3 und Anleiherenditen des Euroraums. Kein Schlüssel, keine Anmeldung.

> Gebaut von Mohammad Abbasi als Teil der "Germany MCP factory". Nicht mit data-api.ecb.europa.eu verbunden.

## Für KI-Agenten

Zur MCP-Client-Konfiguration hinzufügen (stdio):

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

Oder lokal starten: `python -m ecb_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|-------------|
| `ecb_exchange_rates` | Euro-Wechselkurse gegenüber wichtigen Währungen |
| `ecb_interest_rates` | EZB-Leitzinsen (Hauptrefinanzierung, Einlage, Spitzenrefinanzierung) |
| `ecb_inflation` | HVPI-Inflation, Euroraum und Deutschland |
| `ecb_money_supply` | Geldmenge des Euroraums (M1, M2, M3) |
| `ecb_bond_yields` | Staatsanleiherenditen des Euroraums nach Laufzeit |
| `ecb_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## Lizenz

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
