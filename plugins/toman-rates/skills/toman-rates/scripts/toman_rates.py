#!/usr/bin/env python3
"""Print currency rates in Toman from one or more sources (iran-market.github.io by default).

Standard library only; requires Python 3.8+.

To add a source, write a function that takes no arguments and returns Rates, and
register it with @source("name"); see iran_market() below. Raise SourceError when
the source can't be read. Private sources and APIs go in private_sources.py
next to this script, which is gitignored and loaded if present (see load_private_sources()).
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

USER_AGENT = "Mozilla/5.0"
TIMEOUT = 20  # seconds, per request
DEFAULT_CURRENCIES = "USD,CAD,EUR"

CODE_RE = re.compile(r"[A-Z]{3}")

# Maps a currency code (e.g. "USD") to its rate in Toman per unit.
Rates = Dict[str, Union[int, float]]
Fetch = Callable[[], Rates]


class SourceError(Exception):
    pass


# Registered sources, in registration order, which is also the output order.
SOURCES: Dict[str, Fetch] = {}


def source(name: str) -> Callable[[Fetch], Fetch]:
    """Registers fetch as a source called name."""

    def register(fetch: Fetch) -> Fetch:
        if name in SOURCES:
            raise ValueError(f"duplicate source {name!r}")
        SOURCES[name] = fetch
        return fetch

    return register


def get(url: str) -> bytes:
    """Fetches url, turning non-200 responses and network errors into SourceError."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            if resp.status != 200:
                raise SourceError(f"request {url}: status {resp.status} {resp.reason}")
            return resp.read()
    except OSError as e:  # includes URLError, HTTPError and timeouts
        raise SourceError(f"request {url}: {e}") from e


def get_json(url: str) -> Any:
    try:
        return json.loads(get(url))
    except ValueError as e:
        raise SourceError(f"decode {url}: {e}") from e


def number(v: Any) -> Optional[Union[int, float]]:
    """Returns v as an int if it's a whole number, as a float otherwise, or None if it isn't a positive number."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not v > 0:
        return None
    return int(v) if float(v).is_integer() else v


IRAN_MARKET_URL = "https://raw.githubusercontent.com/iran-market/iran-market.github.io/main/data/latest-toman.json"
# Currency symbols: USD_IRR_FREE for the main ones, PRICE_ARS for the rest.
IRAN_MARKET_MAIN_RE = re.compile(r"([A-Z]{3})_IRR_FREE")
IRAN_MARKET_OTHER_RE = re.compile(r"PRICE_([A-Z]{3})")
# PRICE_<code> symbols in the currency category that are crypto tokens, not currencies.
IRAN_MARKET_NON_CURRENCY = {"BCH", "EOS", "ETC", "GNT", "OMG"}


@source("iran-market")
def iran_market() -> Rates:
    """iran-market.github.io: free-market rates in Toman, updated every 30 minutes."""
    return iran_market_rates(get_json(IRAN_MARKET_URL))


def iran_market_rates(d: Any) -> Rates:
    """Extracts every Toman currency rate from a latest-toman.json document, per single unit.

    Entries that don't parse are skipped, so one odd entry can't fail the source.
    A USD_IRR_FREE symbol wins over a PRICE_USD one for the same code.
    """
    try:
        items = d["data"]["categories"]["currency"]
    except (KeyError, TypeError) as e:
        raise SourceError(
            "decode iran-market json: missing data.categories.currency"
        ) from e
    if not isinstance(items, list):
        raise SourceError("decode iran-market json: currency is not a list")
    main: Rates = {}
    other: Rates = {}
    for item in items:
        if (
            not isinstance(item, dict)
            or item.get("currency") != "IRT"
            or not isinstance(item.get("symbol"), str)
        ):
            continue
        price, size = number(item.get("price")), number(item.get("unit_size", 1))
        if price is None or size is None:
            continue
        rate = number(price / size) if size != 1 else price
        if rate is None:
            continue
        m = IRAN_MARKET_MAIN_RE.fullmatch(item["symbol"])
        if m:
            main[m.group(1)] = rate
            continue
        m = IRAN_MARKET_OTHER_RE.fullmatch(item["symbol"])
        if m and m.group(1) not in IRAN_MARKET_NON_CURRENCY:
            other[m.group(1)] = rate
    r = {**other, **main}
    if not r:
        raise SourceError("no currencies in iran-market json")
    return r


def parse_list(s: str) -> List[str]:
    """Splits a comma-separated list, trimming fields and dropping duplicates."""
    out: List[str] = []
    for f in s.split(","):
        f = f.strip()
        if f not in out:
            out.append(f)
    return out


def parse_currencies(s: str) -> Optional[List[str]]:
    """Parses a comma-separated list of currency codes, case-insensitively.

    Returns None for "ALL", meaning every currency any source has.
    """
    codes = parse_list(s.upper())
    if "ALL" in codes:
        if len(codes) > 1:
            raise ValueError("ALL cannot be combined with other currencies")
        return None
    for code in codes:
        if not CODE_RE.fullmatch(code):
            raise ValueError(
                f"invalid currency {code!r}: must be a 3-letter code such as USD, or ALL"
            )
    return codes


def parse_sources(s: str) -> List[str]:
    """Parses a comma-separated list of source names; each must be registered."""
    names = parse_list(s.lower())
    for name in names:
        if name not in SOURCES:
            raise ValueError(
                f"unknown source {name!r}: choose from {', '.join(SOURCES)}"
            )
    return names


def available(want: Optional[List[str]], results: List[Tuple[str, Rates]]) -> List[str]:
    """Returns the codes from want that at least one result has, keeping want's order.

    A None want means every code any result has, sorted.
    """
    have = {code for _, rates in results for code in rates}
    if want is None:
        return sorted(have)
    return [code for code in want if code in have]


def comma(n: Union[int, float]) -> str:
    """Formats n with thousands separators."""
    return f"{n:,}"


def render(fmt: str, codes: List[str], results: List[Tuple[str, Rates]]) -> str:
    """Renders the codes of each result; a missing code is "-" in text, an empty CSV cell, or no JSON key."""
    if fmt == "json":
        out = {
            name: {code: rates[code] for code in codes if code in rates}
            for name, rates in results
        }
        return json.dumps(out, indent=2) + "\n"
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["source", *codes])
        for name, rates in results:
            w.writerow([name, *(rates.get(code, "") for code in codes)])
        return buf.getvalue()
    # A table with a row per currency and a column per source.
    rows = [["Toman", *(name for name, _ in results)]]
    for code in codes:
        rows.append(
            [
                code,
                *(comma(rates[code]) if code in rates else "-" for _, rates in results),
            ]
        )
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines = []
    for row in rows:
        cells = [row[0].ljust(widths[0])] + [
            cell.rjust(widths[i]) for i, cell in enumerate(row) if i > 0
        ]
        lines.append("   ".join(cells))
    return "\n".join(lines) + "\n"


PRIVATE_SOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "private_sources.py")


def load_private_sources(path: str = PRIVATE_SOURCES) -> None:
    """Runs the optional private sources file, which registers its own sources with @source.

    The file does "from toman_rates import source, ..."; that has to get this module even
    when it runs as __main__, or the sources would land in a second copy of SOURCES.
    """
    if "private_sources" in sys.modules or not os.path.exists(path):
        return
    sys.modules.setdefault("toman_rates", sys.modules[__name__])
    spec = importlib.util.spec_from_file_location("private_sources", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["private_sources"] = mod
    spec.loader.exec_module(mod)


def main(argv: Optional[List[str]] = None) -> int:
    load_private_sources()
    parser = argparse.ArgumentParser(
        description="Print currency rates in Toman.",
        epilog="Exit status is 1 if no source could be read, none of the currencies were found, "
        "or output failed, and 2 on bad usage.",
    )
    parser.add_argument(
        "-c",
        "--currencies",
        default=DEFAULT_CURRENCIES,
        metavar="LIST",
        help=f"comma-separated currency codes (default {DEFAULT_CURRENCIES}), or ALL for every currency any source has",
    )
    parser.add_argument(
        "-s",
        "--sources",
        default=",".join(SOURCES),
        metavar="LIST",
        help=f"comma-separated sources to read (default all: {', '.join(SOURCES)})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="text",
        choices=["text", "json", "csv"],
        help="output format (default text)",
    )
    args = parser.parse_args(argv)
    try:
        want = parse_currencies(args.currencies)
        names = parse_sources(args.sources)
    except ValueError as e:
        parser.error(str(e))

    # Sources are fetched concurrently; results keep the order of names.
    with ThreadPoolExecutor(max_workers=len(names)) as pool:
        futures = [(name, pool.submit(SOURCES[name])) for name in names]
    ok: List[Tuple[str, Rates]] = []
    for name, fut in futures:
        try:
            ok.append((name, fut.result()))
        except SourceError as e:
            print(f"{name}: error: {e}", file=sys.stderr)
    if not ok:
        print("no source could be read", file=sys.stderr)
        return 1

    codes = available(want, ok)
    for code in want or []:
        if code not in codes:
            print(f"no rate for {code}", file=sys.stderr)
    if not codes:
        print("none of the currencies were found", file=sys.stderr)
        return 1

    try:
        sys.stdout.write(render(args.output, codes, ok))
        sys.stdout.flush()
    except OSError as e:
        print(f"write output: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
