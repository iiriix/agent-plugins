# agent-plugins

Plugins and [Agent Skills](https://agentskills.io). Each plugin installs on its own and follows the [Agent Plugins specification](https://agent-plugins.org/specification).

| Plugin | Contains | Description |
|--------|----------|-------------|
| [toman-rates](plugins/toman-rates/) | 1 skill | Live currency rates in Iranian Toman from the free iran-market.github.io feed, with pluggable sources: USD, CAD and EUR by default, or any of the 140+ currencies listed. Needs Python 3.8+. |

## Install

**Claude Code:**

```
/plugin marketplace add iiriix/agent-plugins
/plugin install toman-rates@iiriix
```

**Other agents (skills):** with the [skills CLI](https://skills.sh), `npx skills add iiriix/agent-plugins` lets you pick which skills to install and for which agents. Or copy a skill's folder (for example `plugins/toman-rates/skills/toman-rates/`) into the agent's skills directory, such as `~/.config/opencode/skills/` for OpenCode.

**Tools that load Agent Plugins:** point them at the plugin's folder, for example `plugins/toman-rates/`.

## toman-rates

The skill runs `plugins/toman-rates/skills/toman-rates/scripts/toman_rates.py`, which also works on its own:

```sh
S=plugins/toman-rates/skills/toman-rates/scripts/toman_rates.py
python3 $S                    # USD, CAD and EUR
python3 $S -c gbp,try,aed     # -c/--currencies; ALL for every currency
python3 $S -o json            # -o/--output text|json|csv, -h for help
python3 $S -s iran-market     # -s/--sources; default all registered sources
```

```
Toman   iran-market
USD         271,905
CAD         194,310
EUR         305,360
```

## Development

```sh
python3 -m unittest discover -s tests                   # all tests, plus checks on every plugin.json, SKILL.md and the marketplace
claude plugin validate --strict .                       # marketplace manifest
claude plugin validate --strict plugins/<name>/skills   # one plugin's skills
```

See [AGENTS.md](AGENTS.md) for how to add a plugin and release a new version, and [CHANGELOG.md](CHANGELOG.md) for changes.

## License

[MIT](LICENSE)
