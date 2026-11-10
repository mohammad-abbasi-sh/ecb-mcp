# ecb-mcp 💶

mcp-name: io.github.mohammad-abbasi-sh/ecb-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[data-api.ecb.europa.eu](https://data-api.ecb.europa.eu)** — داده‌های بانک مرکزی اروپا از API رسمی SDMX بانک مرکزی اروپا (رایگان، بدون کلید): نرخ‌های ارز یورو، نرخ‌های کلیدی بهره، تورم HICP، عرضهٔ پول M3 و بازده اوراق قرضهٔ منطقهٔ یورو. بدون کلید، بدون ورود.

> ساختهٔ محمد عباسی، بخشی از «کارخانهٔ MCP آلمان». وابسته به data-api.ecb.europa.eu نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP کلاینت اضافه کنید (stdio):

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

یا به‌صورت محلی اجرا کنید: `python -m ecb_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `ecb_exchange_rates` | نرخ‌های ارز یورو در برابر ارزهای اصلی |
| `ecb_interest_rates` | نرخ‌های کلیدی بهرهٔ بانک مرکزی اروپا |
| `ecb_inflation` | تورم HICP منطقهٔ یورو و آلمان |
| `ecb_money_supply` | عرضهٔ پول منطقهٔ یورو (M1، M2، M3) |
| `ecb_bond_yields` | بازده اوراق قرضهٔ دولتی منطقهٔ یورو بر اساس سررسید |
| `ecb_health` | بررسی دسترس‌پذیری (ok / blocked / error) — یک درخواست مؤدبانه |

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## لایسنس

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
