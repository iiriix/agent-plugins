import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plugins", "toman-rates", "skills", "toman-rates", "scripts"))

import toman_rates as tr  # noqa: E402


class TestComma(unittest.TestCase):
    def test_comma(self):
        for n, want in [
            (0, "0"),
            (999, "999"),
            (1000, "1,000"),
            (123456, "123,456"),
            (1234567, "1,234,567"),
            (-999, "-999"),
            (-1234567, "-1,234,567"),
            (1736.31, "1,736.31"),
        ]:
            self.assertEqual(tr.comma(n), want, n)


class TestNumber(unittest.TestCase):
    def test_number(self):
        for v, want in [(5, 5), (5.0, 5), (7.5, 7.5), (0, None), (-1, None), (True, None), ("5", None), (None, None)]:
            got = tr.number(v)
            self.assertEqual(got, want, v)
            self.assertIs(type(got), type(want), v)


class TestParseCurrencies(unittest.TestCase):
    def test_valid(self):
        for s, want in [
            ("USD,CAD,EUR", ["USD", "CAD", "EUR"]),
            (" usd , Gbp ", ["USD", "GBP"]),
            ("USD,usd", ["USD"]),
            ("ALL", None),
            ("all", None),
        ]:
            self.assertEqual(tr.parse_currencies(s), want, s)

    def test_invalid(self):
        for s in ["ALL,USD", "US", "USD,", ""]:
            with self.assertRaises(ValueError, msg=s):
                tr.parse_currencies(s)


class TestParseSources(unittest.TestCase):
    def test_valid(self):
        for s, want in [("iran-market", ["iran-market"]), (" Iran-Market ,iran-market", ["iran-market"])]:
            self.assertEqual(tr.parse_sources(s), want, s)

    def test_invalid(self):
        for s in ["foo", "iran-market,", ""]:
            with self.assertRaises(ValueError, msg=s):
                tr.parse_sources(s)


class TestSource(unittest.TestCase):
    def test_register(self):
        def fetch():
            return {"USD": 1}

        self.addCleanup(tr.SOURCES.pop, "test-source", None)
        self.assertIs(tr.source("test-source")(fetch), fetch)
        self.assertIs(tr.SOURCES["test-source"], fetch)
        with self.assertRaises(ValueError):
            tr.source("test-source")(fetch)


def item(symbol, price, unit_size=1, currency="IRT"):
    return {"symbol": symbol, "price": price, "unit_size": unit_size, "currency": currency}


class TestIranMarketRates(unittest.TestCase):
    def test_rates(self):
        d = {
            "data": {
                "categories": {
                    "currency": [
                        item("USD_IRR_FREE", 271905),
                        item("PRICE_USD", 1),
                        item("PRICE_ARS", 179),
                        item("JPY_IRR_FREE", 173631, unit_size=100),
                        item("PRICE_VND", 7.5),
                        item("PRICE_BCH", 34563960),
                        item("PRICE_DOLLAR_SM", 17940),
                        item("DIFF_USD_TRY", 4.95864),
                        item("EUR_IRR_FREE", "n/a"),
                        item("GBP_IRR_FREE", 0),
                        item("CAD_IRR_FREE", 194310, currency="USD"),
                        item("AED_IRR_FREE", 74589, unit_size=None),
                        "junk",
                    ]
                }
            }
        }
        self.assertEqual(
            tr.iran_market_rates(d), {"USD": 271905, "ARS": 179, "JPY": 1736.31, "VND": 7.5}
        )

    def test_errors(self):
        for d in [
            {"data": {"categories": {"currency": []}}},
            {"data": {"categories": {"currency": {}}}},
            {"data": {"categories": {}}},
            {},
            [],
            None,
        ]:
            with self.assertRaises(tr.SourceError, msg=d):
                tr.iran_market_rates(d)


class TestAvailable(unittest.TestCase):
    def test_available(self):
        results = [("a", {"USD": 1, "EUR": 2}), ("b", {"USD": 1, "ARS": 3})]
        for want, got in [
            (["EUR", "USD", "XYZ", "ARS"], ["EUR", "USD", "ARS"]),
            (["XYZ"], []),
            (None, ["ARS", "EUR", "USD"]),
        ]:
            self.assertEqual(tr.available(want, results), got, want)


class TestRender(unittest.TestCase):
    codes = ["USD", "ARS", "VND"]
    results = [("a", {"USD": 269700}), ("iran-market", {"USD": 271905, "ARS": 179, "VND": 7.5})]

    def test_formats(self):
        for fmt, want in [
            (
                "text",
                "Toman         a   iran-market\n"
                "USD     269,700       271,905\n"
                "ARS           -           179\n"
                "VND           -           7.5\n",
            ),
            (
                "json",
                '{\n  "a": {\n    "USD": 269700\n  },\n'
                '  "iran-market": {\n    "USD": 271905,\n    "ARS": 179,\n    "VND": 7.5\n  }\n}\n',
            ),
            ("csv", "source,USD,ARS,VND\na,269700,,\niran-market,271905,179,7.5\n"),
        ]:
            self.assertEqual(tr.render(fmt, self.codes, self.results), want, fmt)


if __name__ == "__main__":
    unittest.main()
