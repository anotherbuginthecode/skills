#!/usr/bin/env python3
"""Sync skills/<category>/<skill-name>/ into plugins/<skill-name>/ so each
skill becomes an individually installable Claude Code plugin, and regenerate
.claude-plugin/marketplace.json to list them all.

skills/ is the source of truth: this is where you write and edit skills,
organized by category for humans browsing the repo. plugins/ and
.claude-plugin/marketplace.json are build output - never hand-edit them,
re-run this script instead after adding, renaming, or editing a skill.

A Claude Code plugin must have its SKILL.md under exactly
<plugin-root>/skills/<skill-name>/SKILL.md (one level, no custom path
override exists for skills unlike commands/agents/hooks), so a two-level
skills/<category>/<skill-name>/ tree cannot be a marketplace source
directly - hence this sync step.

Usage: python3 scripts/sync_plugins.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
PLUGINS_DIR = REPO_ROOT / "plugins"
MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

# Categories under skills/ that are real folder organization but should
# never be published as installable plugins.
EXCLUDED_CATEGORIES = {"deprecated", "in-progress"}

MARKETPLACE_NAME = "skills"
MARKETPLACE_DESCRIPTION = "Alessandro Mangone's personal Claude Code skills marketplace."
MARKETPLACE_OWNER = {"name": "Alessandro Mangone", "email": "alessandromangone.dev@gmail.com"}


def parse_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"{skill_md} has no YAML frontmatter")
    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        frontmatter[key.strip()] = value
    return frontmatter


def find_skills() -> list[tuple[str, str, Path]]:
    """Returns (category, skill_name, skill_dir) for every publishable
    skills/<category>/<skill_name>/SKILL.md, skipping EXCLUDED_CATEGORIES."""
    found = []
    for skill_md in sorted(SKILLS_DIR.glob("*/*/SKILL.md")):
        skill_dir = skill_md.parent
        category = skill_dir.parent.name
        skill_name = skill_dir.name
        if category in EXCLUDED_CATEGORIES:
            continue
        found.append((category, skill_name, skill_dir))
    return found


def sync_plugin(category: str, skill_name: str, skill_dir: Path) -> dict:
    plugin_dir = PLUGINS_DIR / skill_name

    dest_skill_dir = plugin_dir / "skills" / skill_name
    shutil.copytree(skill_dir, dest_skill_dir)

    frontmatter = parse_frontmatter(skill_dir / "SKILL.md")
    description = frontmatter.get("description", "")

    plugin_json = {
        "name": skill_name,
        "description": description,
        "version": "0.1.0",
    }
    claude_plugin_dir = plugin_dir / ".claude-plugin"
    claude_plugin_dir.mkdir(parents=True, exist_ok=True)
    (claude_plugin_dir / "plugin.json").write_text(
        json.dumps(plugin_json, indent=2) + "\n", encoding="utf-8"
    )

    return {
        "name": skill_name,
        "description": description,
        "category": category,
        "source": f"./plugins/{skill_name}",
    }


def main() -> None:
    skills = find_skills()
    if not skills:
        print("No publishable skills found under skills/*/*/SKILL.md", file=sys.stderr)
        sys.exit(1)

    seen_names: set[str] = set()
    for _, skill_name, _ in skills:
        if skill_name in seen_names:
            print(f"Duplicate skill name across categories: {skill_name}", file=sys.stderr)
            sys.exit(1)
        seen_names.add(skill_name)

    # plugins/ is fully derived from skills/ - wipe and rebuild rather than
    # patch, so a renamed or removed skill can never leave a stale plugin
    # behind.
    if PLUGINS_DIR.exists():
        shutil.rmtree(PLUGINS_DIR)
    PLUGINS_DIR.mkdir(parents=True)

    plugin_entries = [
        sync_plugin(category, skill_name, skill_dir)
        for category, skill_name, skill_dir in skills
    ]

    marketplace = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": MARKETPLACE_NAME,
        "description": MARKETPLACE_DESCRIPTION,
        "owner": MARKETPLACE_OWNER,
        "plugins": plugin_entries,
    }
    MARKETPLACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKETPLACE_PATH.write_text(json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")

    print(f"Synced {len(plugin_entries)} plugin(s) into {PLUGINS_DIR.relative_to(REPO_ROOT)}/")
    for entry in plugin_entries:
        print(f"  - {entry['name']} ({entry['category']})")
    print(f"Regenerated {MARKETPLACE_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
