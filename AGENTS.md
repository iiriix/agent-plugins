# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, OpenCode and others) working in this repository. `CLAUDE.md` is a symlink to this file.

## Overview

`iiriix/agent-plugins` is a marketplace of independently installable plugins. Every entry, including one that is just a single skill, is a plugin folder under `plugins/<name>/` laid out per the [Agent Plugins specification](https://agent-plugins.org/specification) (v1.0.0):

```
plugins/<name>/plugin.json                  manifest: $schema, name, version, description, ...
plugins/<name>/skills/<skill>/SKILL.md      Agent Skills format (https://agentskills.io), plus bundled files such as scripts/
plugins/<name>/mcp.json                     MCP servers, if any
```

- The spec defines no marketplace, so `.claude-plugin/marketplace.json` (Claude Code marketplace `iiriix`) is the catalog: one entry per plugin with `"source": "./plugins/<name>"` and `"strict": false`. Claude Code ignores `plugin.json`, uses the entry as the manifest, and finds the plugin's `skills/` folder on its own, so the entry has no `skills` field. Other tools load a plugin by its folder.
- The spec only covers skills and `mcp.json`. Claude-only components (`agents/`, `commands/`, `hooks/`) work in Claude Code but aren't portable.
- Each skill must work when its own folder is copied elsewhere (that's how OpenCode and `npx skills add` use it), so it can't reference files outside that folder.

`tests/` sits outside `plugins/` so tests don't ship, and mirrors it: repo-wide checks at the top, a plugin's tests in `tests/plugins/test_<name>.py` (module names use underscores; each folder needs an `__init__.py` for unittest). `tests/test_marketplace.py` checks every `plugin.json` against the spec's rules, every `SKILL.md`'s frontmatter, that each plugin has exactly one marketplace entry, and that the entry's `version`, `description` and `license` match `plugin.json`.

## Commands

```sh
python3 -m unittest discover -s tests                         # all tests
python3 -m unittest tests.plugins.test_toman_rates.TestRender # one test class
claude plugin validate --strict .                             # marketplace manifest
claude plugin validate --strict plugins/<name>/skills         # one plugin's SKILL.md files
```

## Adding a plugin

1. Create `plugins/<name>/plugin.json` with `"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"`, `name` (equal to the folder; lowercase letters, digits, `-` and `.`, at most 64 characters), `version` starting at `0.1.0`, `description`, `author`, `homepage`, `repository`, `"license": "MIT"` and `keywords`. The spec's schema is closed: no other top-level fields.
2. Add skills as `plugins/<name>/skills/<skill>/SKILL.md`. The skill `name` must equal its folder (lowercase letters, digits and hyphens, at most 64 characters), and `description` (at most 1024 characters) says what it does and when to use it, since that's what the agent matches against. Put scripts in the skill's `scripts/` and refer to them relative to the skill folder; prefer standard-library Python so it runs anywhere. A single-skill plugin usually uses the same name for the plugin and the skill.
3. Add a marketplace entry with the same `name`, `version`, `description` and `license` as `plugin.json`, plus `author`, `homepage`, `repository`, `keywords`, `"source": "./plugins/<name>"` and `"strict": false`.
4. Add `plugins/<name>/README.md` (what it does, how to install it, requirements), tests as `tests/plugins/test_<name>.py`, a row to the root README's table, and a section to `CHANGELOG.md`.

## Releasing

Each plugin is versioned on its own; installs follow `main`, so `main` should always be releasable. There are no git tags or GitHub releases: a release is the version bump landing on `main`. For each plugin that changed, and only those:

1. Bump its `version` (semver) in both `plugin.json` and its `marketplace.json` entry (the tests fail if they differ), or users may not get the update.
2. Add the changes under its section in `CHANGELOG.md`.

## toman-rates

A single-skill plugin. `plugins/toman-rates/skills/toman-rates/scripts/toman_rates.py` is a single-file Python CLI, standard library only, that must keep working on Python 3.8. It gets currency rates in Toman (USD, CAD and EUR by default) from pluggable sources, iran-market.github.io by default, and prints text, JSON or CSV. Keep its `SKILL.md` and README in step: update them when flags, output format, sources, currencies or exit codes change.

```sh
S=plugins/toman-rates/skills/toman-rates/scripts/toman_rates.py
python3 $S                 # text output
python3 $S -o json         # or --output json|csv
python3 $S -c gbp,try      # or --currencies; ALL for every currency
python3 $S -s iran-market  # or --sources; default all registered sources
```

- A source is a function taking no arguments and returning `Rates` (currency code → Toman per single unit, `int`, or `float` when not whole), registered with `@source("name")` into `SOURCES`. Registration order is the default `-s` order and the output order. Fetch with `get()`/`get_json()`, which set the User-Agent, apply the 20s timeout and turn non-200 responses, network errors and bad JSON into `SourceError`.
- Each source returns every currency it has; entries that don't parse are skipped rather than failing the source, and finding no currencies at all is a `SourceError`. `number()` normalises values (positive numbers only; whole floats become `int`). `main` then filters to the `-c` list via `available()`: requested order for a list, sorted for `ALL`. A requested code that no source has is reported to stderr as `no rate for XXX`.
- Private sources and APIs (keyed or paid APIs, internal feeds, anything that stays out of the repo) go in `scripts/private_sources.py` next to the script (gitignored; never commit it). `load_private_sources()`, called at the start of `main`, runs it if present. It registers sources with `@source` via `from toman_rates import ...`, which works when the script runs as `__main__` because the loader first aliases `sys.modules["toman_rates"]` to the running module. A broken private file raises rather than being skipped. Tests don't load it.
- **iran-market**: reads `latest-toman.json` from raw.githubusercontent.com (updated every 30 minutes), `data.categories.currency[]` entries with `currency` `IRT`. Symbols `XXX_IRR_FREE` (`IRAN_MARKET_MAIN_RE`) win over `PRICE_XXX` (`IRAN_MARKET_OTHER_RE`); the crypto tokens in `IRAN_MARKET_NON_CURRENCY` and longer symbols (dollar variants, `DIFF_*` ratios) are ignored. `price` is divided by `unit_size` (JPY is quoted per 100). `stale` entries are kept, since the feed marks rates stale while the market is closed.
- Sources are fetched concurrently, and results keep the `-s` order. A failing source is reported to stderr and skipped. The exit code is 0 if at least one source succeeded and at least one requested currency was found, 1 if no source succeeded, no currency was found or writing stdout failed, and 2 for an invalid `-o`, `-c` or `-s` value (via argparse).
- `render()` returns the whole output as a string, written to stdout in one checked write. Text is a table with a row per currency and a column per source, `-` where a source lacks one. JSON relies on dict insertion order to keep source and currency order stable; keep that if you change the output.
