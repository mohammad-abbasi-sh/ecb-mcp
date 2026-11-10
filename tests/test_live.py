"""Live tests — hit the real ECB SDMX API. Cautious: few requests.
The ECB API 504s intermittently; http.py retries 429/5xx once.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set ECB_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from ecb_mcp import server as srv

pytestmark = pytest.mark.live
SKIP = os.environ.get("ECB_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="ECB_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_exchange_rates_live(self):
        out = json.loads(srv.ecb_exchange_rates(["USD", "GBP"], limit=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 2)
        self.assertGreater(out["rates"][0]["rate"], 1.0)
        print(f"\nLIVE EUR/USD: {out['rates'][0]['rate']} on {out['rates'][0]['date']}")

    def test_interest_rates_live(self):
        out = json.loads(srv.ecb_interest_rates())
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 3)
        by_code = {r["code"]: r["rate_pct"] for r in out["rates"]}
        self.assertGreater(by_code["MRR_FR"], by_code["DFR"])
        self.assertGreater(by_code["MLFR"], by_code["MRR_FR"])
        print(f"\nLIVE key rates: {by_code}")

    def test_inflation_live(self):
        out = json.loads(srv.ecb_inflation("U2", limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 3)
        self.assertIsNotNone(out["latest"])
        print(f"\nLIVE HICP euro area: {out['latest']}")

    def test_money_supply_live(self):
        out = json.loads(srv.ecb_money_supply("M3", limit=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 3)
        self.assertGreater(out["latest"]["value"], 10000000)
        print(f"\nLIVE M3: {out['latest']}")

    def test_bond_yields_live(self):
        out = json.loads(srv.ecb_bond_yields("10Y", limit=2))
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 2)
        self.assertGreater(out["latest"]["value"], 0)
        print(f"\nLIVE 10Y yield: {out['latest']}")

    def test_health_live(self):
        out = json.loads(srv.ecb_health())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["http_status"], 200)
