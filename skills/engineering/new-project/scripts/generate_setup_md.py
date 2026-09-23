#!/usr/bin/env python3
"""Render SETUP.md: how to get the workflow skills this repo's AGENTS.md
and PR template reference (review always, task-to-pr only if enabled),
each installed however the user said during setup - a plugin marketplace,
an npx package, already in this repo's own skills/ folder, or already
installed globally.

Everything needed comes from the project config written during setup
(see workflow_skills in SKILL.md) - this script does no inference.

Usage: generate_setup_md.py --config <project-config.json> <dest>
"""
import json
import sys


def install_lines(role_label: str, skill: dict) -> list[str]:
    name = skill["name"]
    why = skill.get("why", "")
    source = skill.get("source", {})
    source_type = source.get("type")

    lines = [f"### {role_label}: `/{name}`", ""]
    if why:
        lines.append(why)
        lines.append("")

    if source_type == "marketplace":
        marketplace = source["marketplace"]
        short_name = marketplace.split("/")[-1]
        lines.append(f"    /plugin marketplace add {marketplace}")
        lines.append(f"    /plugin install {name}@{short_name}")
    elif source_type == "npx":
        package = source["package"]
        lines.append(f"    npx {package}")
    elif source_type == "local":
        lines.append("Already in this repo's skills/ folder - no install needed.")
    elif source_type == "global":
        lines.append("Assumed already installed globally on your machine - no action needed.")
    else:
        lines.append(f"Source not recorded - install `{name}` manually.")

    lines.append("")
    return lines


def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] != "--config":
        print("Usage: generate_setup_md.py --config <project-config.json> <dest>", file=sys.stderr)
        sys.exit(1)

    config_path, dest = sys.argv[2], sys.argv[3]
    config = json.loads(open(config_path, encoding="utf-8").read())
    workflow_skills = config.get("workflow_skills", {})

    lines = ["# One-time setup", ""]
    lines.append(
        "AGENTS.md and this repo's PR template assume the skills below. "
        "Claude Code plugin marketplaces are registered per machine, not "
        "committed to the repo, so run the steps below once per machine, "
        "not on every checkout."
    )
    lines.append("")

    review = workflow_skills.get("review")
    if review:
        lines += install_lines("Code review", review)

    task_to_pr = workflow_skills.get("task_to_pr")
    if task_to_pr and task_to_pr.get("enabled"):
        lines += install_lines("Task to PR", task_to_pr)

    open(dest, "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    main()
