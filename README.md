# agent-plugins

Plugins and [Agent Skills](https://agentskills.io). Each plugin installs on its own and follows the [Agent Plugins specification](https://agent-plugins.org/specification).

| Plugin | Contains | Description |
|--------|----------|-------------|
| [toman-rates](plugins/toman-rates/) | 1 skill | Live currency rates in Iranian Toman from the free iran-market.github.io feed. |

## Install

Each plugin installs on its own. See its README, linked in the table, for what it does, its requirements and plugin-specific install commands.

**Claude Code:**

```
/plugin marketplace add iiriix/agent-plugins
/plugin install <plugin>@iiriix
```

**Hermes Agent:** install each skill from its folder. Hermes scans it and asks you to confirm (`--yes` skips the prompt), and `hermes skills update` keeps it up to date.

```sh
hermes skills install iiriix/agent-plugins/plugins/<plugin>/skills/<skill>
```

**Other agents (skills):** with the [skills CLI](https://skills.sh), `npx skills add iiriix/agent-plugins` lets you pick which skills to install and for which agents. Or copy a skill's folder (`plugins/<plugin>/skills/<skill>/`) into the agent's skills directory, such as `~/.config/opencode/skills/` for OpenCode.

**Tools that load Agent Plugins:** point them at the plugin's folder, `plugins/<plugin>/`.

## Development

```sh
python3 -m unittest discover -s tests                   # all tests, plus checks on every plugin.json, SKILL.md and the marketplace
claude plugin validate --strict .                       # marketplace manifest
claude plugin validate --strict plugins/<name>/skills   # one plugin's skills
```

See [AGENTS.md](AGENTS.md) for how to add a plugin and release a new version, and [CHANGELOG.md](CHANGELOG.md) for changes.

## License

[MIT](LICENSE)
