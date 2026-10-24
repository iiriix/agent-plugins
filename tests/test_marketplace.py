"""Checks that every plugin in plugins/ is a valid Agent Plugins plugin and listed in the marketplace exactly once.

Each plugin is plugins/<name>/ with a plugin.json (https://agent-plugins.org/specification) and its skills in
skills/<skill>/SKILL.md. Its .claude-plugin/marketplace.json entry uses "source": "./plugins/<name>".
"""

import json
import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
PLUGINS_DIR = os.path.join(ROOT, "plugins")
MARKETPLACE = os.path.join(ROOT, ".claude-plugin", "marketplace.json")

# From https://agent-plugins.org/schemas/1.0.0/plugin.schema.json.
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PLUGIN_NAME_RE = re.compile(r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?")
PLUGIN_FIELDS = {
    "$schema", "name", "version", "description", "author", "homepage", "repository", "license", "keywords", "extensions",
}
# From https://agentskills.io/specification.
SKILL_NAME_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
SEMVER_RE = re.compile(r"\d+\.\d+\.\d+")


def frontmatter(path):
    """Returns the top-level key: value pairs of a SKILL.md frontmatter block."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError(f"{path}: no frontmatter")
    fields = {}
    for line in m.group(1).splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def subdirs(path):
    if not os.path.isdir(path):
        return []
    return sorted(d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and d != "__pycache__")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_entries():
    return load_json(MARKETPLACE)["plugins"]


class TestPlugins(unittest.TestCase):
    def test_manifest(self):
        for name in subdirs(PLUGINS_DIR):
            with self.subTest(plugin=name):
                m = load_json(os.path.join(PLUGINS_DIR, name, "plugin.json"))
                self.assertEqual(m.get("$schema"), PLUGIN_SCHEMA)
                self.assertEqual(m.get("name"), name, "name must match the folder name")
                self.assertRegex(name, PLUGIN_NAME_RE)
                self.assertLessEqual(len(name), 64)
                self.assertRegex(m.get("version", ""), SEMVER_RE)
                self.assertTrue(m.get("description"), "description is required here, though the spec allows omitting it")
                self.assertTrue(m.get("license"), "license is required here, though the spec allows omitting it")
                self.assertLessEqual(set(m), PLUGIN_FIELDS, "unknown top-level fields")

    def test_skills(self):
        for plugin in subdirs(PLUGINS_DIR):
            skills_dir = os.path.join(PLUGINS_DIR, plugin, "skills")
            for name in subdirs(skills_dir):
                with self.subTest(skill=f"{plugin}/{name}"):
                    fm = frontmatter(os.path.join(skills_dir, name, "SKILL.md"))
                    self.assertEqual(fm.get("name"), name, "name must match the folder name")
                    self.assertRegex(name, SKILL_NAME_RE)
                    self.assertLessEqual(len(name), 64)
                    self.assertTrue(fm.get("description"), "description is required")
                    self.assertLessEqual(len(fm["description"]), 1024)


class TestMarketplace(unittest.TestCase):
    def test_every_plugin_listed_once(self):
        names = [e["name"] for e in load_entries()]
        self.assertEqual(len(names), len(set(names)), "plugin names must be unique")
        self.assertEqual(sorted(names), subdirs(PLUGINS_DIR), "each plugins/<name> needs exactly one marketplace entry")

    def test_entries_match_manifests(self):
        for e in load_entries():
            name = e["name"]
            with self.subTest(plugin=name):
                self.assertEqual(e.get("source"), f"./plugins/{name}")
                self.assertNotIn("skills", e, "skills are found in the plugin's skills/ folder, as in the spec")
                m = load_json(os.path.join(PLUGINS_DIR, name, "plugin.json"))
                for field in ("version", "description", "license"):
                    self.assertEqual(e.get(field), m.get(field), f"{field} differs between marketplace.json and plugin.json")


if __name__ == "__main__":
    unittest.main()
