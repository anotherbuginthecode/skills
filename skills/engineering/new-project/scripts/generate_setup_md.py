#!/usr/bin/env python3
"""Render SETUP.md: the one-time Claude Code plugin marketplace setup steps
for the skills this repo's AGENTS.md and templates assume are installed.

Reads the skill list from references/default-skills.json, so adding a skill
there is enough to make every future bootstrapped repo suggest it - no
change needed here.

Usage: generate_setup_md.py <default-skills.json> <dest>
"""
import json
import sys


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: generate_setup_md.py <default-skills.json> <dest>", file=sys.stderr)
        sys.exit(1)

    skills_path, dest = sys.argv[1], sys.argv[2]
    skills = json.loads(open(skills_path, encoding="utf-8").read())

    marketplaces = sorted({s["marketplace"] for s in skills})

    lines = ["# One-time setup", ""]
    lines.append(
        "AGENTS.md and this repo's issue/PR templates assume the skills below "
        "are installed. Claude Code plugin marketplaces are registered per "
        "machine, not per repo, so run this once per marketplace, not on "
        "every checkout."
    )
    lines.append("")
    lines.append("## 1. Add the marketplace")
    lines.append("")
    for mp in marketplaces:
        lines.append(f"    /plugin marketplace add {mp}")
    lines.append("")
    lines.append("## 2. Install the skills this repo uses")
    lines.append("")
    for s in skills:
        short_name = s["marketplace"].split("/")[-1]
        lines.append(f"    /plugin install {s['slug']}@{short_name}")
        lines.append(f"    # {s['why']}")
        lines.append("")

    open(dest, "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    main()
