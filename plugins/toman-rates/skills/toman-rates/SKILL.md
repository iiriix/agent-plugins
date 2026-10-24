---
name: toman-rates
description: Fetch live exchange rates in Iranian Toman (USD, EUR, CAD, GBP, AED, TRY and over 100 more) from the free iran-market.github.io data feed using a bundled Python script. Use when the user asks for the current dollar, euro or any other foreign currency rate in Toman or Rial, the Iranian free-market rate, or wants to convert between a foreign currency and Toman or Rial.
license: MIT
compatibility: Requires Python 3.8+ (standard library only) and network access to raw.githubusercontent.com.
---

# Toman rates

Gets current free-market rates for foreign currencies in Toman with the bundled script `scripts/toman_rates.py`. The built-in source is `iran-market` ([iran-market.github.io](https://iran-market.github.io), free-market data updated every 30 minutes).

## Run it

The script path is relative to this skill's directory:

```sh
python3 scripts/toman_rates.py -c USD,EUR -o json
```

It makes one web request per source and usually finishes in a few seconds (each request times out after 20 seconds).

- `-c`/`--currencies` takes comma-separated ISO 4217 codes, case-insensitive (default `USD,CAD,EUR`). Ask only for the currencies the user needs.
- `-c ALL` returns every currency the sources have (over 100). Use it only when the user wants the full list, or to find out whether a currency is available.
- `-s`/`--sources` picks sources by name (default: all of them). `--help` lists them.

Use `-o json` when you need to read or compute with the values. Use `text` (the default) or `csv` only when the user asks for that format.

## Output

JSON, one object per source that succeeded. Currencies keep the order given to `-c` (alphabetical for `ALL`), and a source that doesn't carry a currency leaves it out. Values are Toman per single unit of the currency: integers, or decimals for low-value currencies and those quoted per 100 units (for example JPY):

```json
{
  "iran-market": {
    "USD": 103500,
    "CAD": 74200,
    "EUR": 120300
  }
}
```

The numbers above are illustrative only; always run the command for real values.

- Multiply by 10 if the user asks for Rial.
- The feed is updated every 30 minutes, and rates stay at the last close while the market is shut (for example on Fridays), so a figure can be a few hours old.

## Exit status and errors

| Exit | Meaning |
|------|---------|
| 0 | At least one source was read and at least one requested currency found. A failed source is reported on stderr as `<source>: error: ...` and left out of the output; a currency no source has is reported as `no rate for XXX` and left out. |
| 1 | No source could be read (`no source could be read`), none of the requested currencies were found (`none of the currencies were found`), or writing output failed. |
| 2 | Invalid `-o` value, currency code (`-c` takes 3-letter codes or `ALL`) or source name. |

If a currency isn't found, tell the user the source doesn't list it. If a source fails, show the stderr message; it's a network call, so a retry may help, but don't loop on it.

## Answering the user

- Say where the numbers came from. If more than one source answered, show each rather than averaging unless asked.
- Format numbers with thousands separators (for example 103,500 Toman).
- Rates change throughout the day; note that the figures are as of when the command ran.
