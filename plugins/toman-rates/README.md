# toman-rates

Live exchange rates in Iranian Toman from the free [iran-market.github.io](https://iran-market.github.io) data feed. Returns USD, CAD and EUR by default, or any of the 140+ currencies it lists.

The plugin has one skill, `toman-rates`. The agent uses it when you ask things like "what's the dollar rate in Toman?" or "convert 500 euros to Rial".

## Install

**Claude Code:**

```
/plugin marketplace add iiriix/agent-plugins
/plugin install toman-rates@iiriix
```

**Hermes Agent:** Hermes installs Agent Plugins disabled, so enable it afterwards. `hermes plugins update` keeps it up to date.

```sh
hermes plugins install iiriix/agent-plugins/plugins/toman-rates --no-enable
hermes plugins enable toman-rates
```

**Other agents:** `npx skills add iiriix/agent-plugins --skill toman-rates`, or copy [`skills/toman-rates/`](skills/toman-rates/) into the agent's skills directory (for OpenCode, `~/.config/opencode/skills/`).

## Requirements

- Python 3.8 or newer (standard library only, nothing to install)
- Network access to raw.githubusercontent.com

## Use the script directly

The skill runs [`skills/toman-rates/scripts/toman_rates.py`](skills/toman-rates/scripts/toman_rates.py), which also works on its own:

```sh
python3 skills/toman-rates/scripts/toman_rates.py                  # USD, CAD and EUR
python3 skills/toman-rates/scripts/toman_rates.py -c gbp,try,aed   # any 3-letter codes, or ALL
python3 skills/toman-rates/scripts/toman_rates.py -o json          # text (default), json or csv
python3 skills/toman-rates/scripts/toman_rates.py -s iran-market   # pick sources (default all)
```

```
Toman   iran-market
USD         271,905
CAD         194,310
EUR         305,360
```

## Adding a source

Sources are pluggable. Add a function to the script that takes no arguments and returns a dict of currency code to Toman per unit, register it with `@source("name")`, and raise `SourceError` if it can't be read. Every registered source runs by default, concurrently, each shown in its own column, and `-s` picks among them:

```python
@source("example")
def example() -> Rates:
    d = get_json("https://example.com/rates.json")  # get()/get_json() raise SourceError on failure
    return {"USD": d["usd"], "EUR": d["eur"]}
```

Check that the source's terms allow this kind of use before adding it.

### Private sources

Private sources and APIs, such as an API that needs your own key or a paid feed, go in `skills/toman-rates/scripts/private_sources.py`. That file is gitignored, and the script loads it if it exists. Write it the same way, importing what it needs from the script:

```python
from toman_rates import Rates, SourceError, get_json, source

@source("example")
def example() -> Rates:
    ...
```

It only takes effect where the file exists, such as your checkout or a skill folder you copied it into. Installs from GitHub never have it.

## Notes on the data

- iran-market.github.io republishes free-market rates as public MIT-licensed JSON, updated every 30 minutes. Rates stay at the last close while the market is shut.
- Values are per single unit: currencies the feed quotes per 100 units (such as JPY) are divided accordingly, and low-value currencies keep their decimals.

## License

[MIT](../../LICENSE)
