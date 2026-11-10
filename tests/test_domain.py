"""Offline tests — parse real captured ECB SDMX-JSON fixtures, no
network. Fixtures are live API responses (2026-11-10); values are
the ECB's own published figures."""
import json
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from ecb_mcp import domain as dom
from ecb_mcp import server as srv

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name):
    return (FIX / name).read_text(encoding="utf-8")


class TestValidators(unittest.TestCase):
    def test_currency(self):
        self.assertEqual(dom.validate_currency("usd"), "USD")
        self.assertEqual(dom.validate_currency("  gbp "), "GBP")
        with self.assertRaises(ValueError):
            dom.validate_currency("US")
        with self.assertRaises(ValueError):
            dom.validate_currency("US1")

    def test_area(self):
        self.assertEqual(dom.validate_area("u2"), "U2")
        self.assertEqual(dom.validate_area("DE"), "DE")
        with self.assertRaises(ValueError):
            dom.validate_area("FR")

    def test_aggregate(self):
        self.assertEqual(dom.validate_aggregate("m3"), "M3")
        with self.assertRaises(ValueError):
            dom.validate_aggregate("M4")

    def test_maturity(self):
        self.assertEqual(dom.validate_maturity("10y"), "10Y")
        with self.assertRaises(ValueError):
            dom.validate_maturity("7Y")

    def test_limit(self):
        self.assertEqual(dom.validate_limit(5), 5)
        with self.assertRaises(ValueError):
            dom.validate_limit(0)
        with self.assertRaises(ValueError):
            dom.validate_limit(31)
        with self.assertRaises(ValueError):
            dom.validate_limit(25, 24)

    def test_urls(self):
        self.assertEqual(dom.exchange_rate_url("USD", 5),
                         "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=5")
        self.assertEqual(dom.key_rate_url("MRR_FR", 1),
                         "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.MRR_FR.LEV?lastNObservations=1")
        self.assertEqual(dom.inflation_url("DE", 6),
                         "https://data-api.ecb.europa.eu/service/data/ICP/M.DE.N.000000.4.ANR?lastNObservations=6")
        self.assertEqual(dom.money_supply_url("M1", 3),
                         "https://data-api.ecb.europa.eu/service/data/BSI/M.U2.Y.V.M10.X.1.U2.2300.Z01.E?lastNObservations=3")
        self.assertEqual(dom.bond_yield_url("2Y", 3),
                         "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y?lastNObservations=3")


class TestFixtures(unittest.TestCase):
    def test_exr_usd(self):
        s = dom.parse_sdmx(_read("exr-usd.json"))
        self.assertEqual(len(s), 1)
        self.assertEqual(len(s[0]["observations"]), 5)
        self.assertEqual(dom.latest_observation(s),
                         {"period": "2026-11-10", "value": 1.1214})

    def test_exr_gbp_jpy(self):
        self.assertEqual(dom.latest_observation(
            dom.parse_sdmx(_read("exr-gbp.json")))["value"], 0.83545)
        self.assertEqual(len(dom.parse_sdmx(_read("exr-jpy.json"))[0]["observations"]), 5)

    def test_key_rates(self):
        self.assertEqual(dom.latest_observation(
            dom.parse_sdmx(_read("fm-mrr.json")))["value"], 2.65)
        self.assertEqual(dom.latest_observation(
            dom.parse_sdmx(_read("fm-dfr.json")))["value"], 2.5)
        self.assertEqual(dom.latest_observation(
            dom.parse_sdmx(_read("fm-mlfr.json")))["value"], 2.9)

    def test_inflation(self):
        u2 = dom.parse_sdmx(_read("icp-u2.json"))
        self.assertEqual(len(u2[0]["observations"]), 6)
        self.assertEqual(dom.latest_observation(u2),
                         {"period": "2025-12", "value": 1.9})
        de = dom.parse_sdmx(_read("icp-de.json"))
        self.assertEqual(dom.latest_observation(de)["value"], 2.0)

    def test_money_supply(self):
        m3 = dom.parse_sdmx(_read("bsi-m3.json"))
        self.assertEqual(dom.latest_observation(m3)["value"], 17717267.0)
        m1 = dom.parse_sdmx(_read("bsi-m1.json"))
        self.assertEqual(dom.latest_observation(m1)["value"], 11333724.0)
        m2 = dom.parse_sdmx(_read("bsi-m2.json"))
        self.assertEqual(len(m2[0]["observations"]), 3)

    def test_bond_yields(self):
        y10 = dom.parse_sdmx(_read("yc-10y.json"))
        self.assertAlmostEqual(dom.latest_observation(y10)["value"], 3.272, places=2)
        y2 = dom.parse_sdmx(_read("yc-2y.json"))
        self.assertAlmostEqual(dom.latest_observation(y2)["value"], 2.939, places=2)
        y30 = dom.parse_sdmx(_read("yc-30y.json"))
        self.assertEqual(len(y30[0]["observations"]), 3)

    def test_bad_json(self):
        with self.assertRaises(ValueError):
            dom.parse_sdmx("{not json")

    def test_error_payload(self):
        with self.assertRaises(ValueError):
            dom.parse_sdmx('{"title": "Not Found", "status": 404, "detail": "No Series"}')


class TestServerOffline(unittest.TestCase):
    """Server tools with fetch_text mocked to the fixtures."""

    def _mock_fetch(self, mapping):
        def fake(url):
            for key, name in mapping.items():
                if key in url:
                    return _read(name)
            raise AssertionError(f"unexpected URL {url}")
        return fake

    def test_exchange_rates(self):
        mapping = {"D.USD.EUR": "exr-usd.json", "D.GBP.EUR": "exr-gbp.json"}
        with mock.patch("ecb_mcp.server._http.fetch_text", self._mock_fetch(mapping)):
            out = json.loads(srv.ecb_exchange_rates(["USD", "GBP"], limit=5))
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 2)
        self.assertEqual(out["rates"][0]["rate"], 1.1214)
        self.assertEqual(out["rates"][0]["pair"], "EUR/USD")
        self.assertEqual(out["source"], "data-api.ecb.europa.eu")
        self.assertIn("fetched_at", out)

    def test_exchange_rates_bad_currency(self):
        out = json.loads(srv.ecb_exchange_rates(["US"], limit=5))
        self.assertIn("error", out)

    def test_interest_rates(self):
        mapping = {"MRR_FR": "fm-mrr.json", "DFR": "fm-dfr.json", "MLFR": "fm-mlfr.json"}
        with mock.patch("ecb_mcp.server._http.fetch_text", self._mock_fetch(mapping)):
            out = json.loads(srv.ecb_interest_rates())
        self.assertNotIn("error", out)
        self.assertEqual(out["total_results"], 3)
        by_code = {r["code"]: r["rate_pct"] for r in out["rates"]}
        self.assertEqual(by_code, {"MRR_FR": 2.65, "DFR": 2.5, "MLFR": 2.9})

    def test_inflation(self):
        with mock.patch("ecb_mcp.server._http.fetch_text",
                        lambda url: _read("icp-u2.json")):
            out = json.loads(srv.ecb_inflation("U2", limit=6))
        self.assertNotIn("error", out)
        self.assertEqual(out["latest"], {"period": "2025-12", "value": 1.9})
        self.assertEqual(out["area_name"], "Euro area")

    def test_inflation_bad_area(self):
        out = json.loads(srv.ecb_inflation("FR"))
        self.assertIn("error", out)

    def test_money_supply(self):
        with mock.patch("ecb_mcp.server._http.fetch_text",
                        lambda url: _read("bsi-m3.json")):
            out = json.loads(srv.ecb_money_supply("M3", limit=6))
        self.assertNotIn("error", out)
        self.assertEqual(out["latest"]["value"], 17717267.0)

    def test_bond_yields(self):
        with mock.patch("ecb_mcp.server._http.fetch_text",
                        lambda url: _read("yc-10y.json")):
            out = json.loads(srv.ecb_bond_yields("10Y", limit=5))
        self.assertNotIn("error", out)
        self.assertAlmostEqual(out["latest"]["value"], 3.272, places=2)

    def test_health_mocked(self):
        with mock.patch("ecb_mcp.server._http.health_check",
                        return_value={"status": "ok", "http_status": 200,
                                      "url": "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?lastNObservations=1"}):
            out = json.loads(srv.ecb_health())
        self.assertEqual(out["status"], "ok")


if __name__ == "__main__":
    unittest.main()
