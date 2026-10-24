# Changelog

Each plugin is versioned on its own with [semver](https://semver.org), in its `plugin.json` and `.claude-plugin/marketplace.json` entry. A release bumps only the plugins that changed; there are no git tags.

## toman-rates

### 0.1.0

- First release: USD, CAD, EUR or any listed currency (`-c`, `ALL`) in Toman from iran-market.github.io, as text, JSON or CSV. Sources are pluggable (`@source`, `-s`).
