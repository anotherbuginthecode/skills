#!/usr/bin/env python3
"""Install every publishable skill globally for every coding agent, by
symlinking skills/<category>/<skill-name>/ into each agent's user-level
skills directory.

Targets (one symlink per skill, never the whole directory):

  ~/.agents/skills   shared cross-agent location - read by Codex and other
                     agents that follow the Agent Skills convention
  ~/.claude/skills   Claude Code (it does not read ~/.agents/skills)

Per-skill symlinks, not a directory-level link like zazencodes/agent-skills,
because these directories already hold skills managed by other installers
(e.g. `npx skills`) and must be left alone. Because the links point at
skills/, editing a skill here is live in every agent immediately - no
re-install needed. Re-run only after adding, renaming, or removing a skill.

Safety: the script only ever creates, replaces, or removes symlinks that
point into this repository. A real file/directory, or a symlink to
somewhere else, with the same name as one of our skills is reported as a
conflict and left untouched.

Usage:
  python3 scripts/install_global.py              # install / refresh
  python3 scripts/install_global.py --dry-run    # show what would change
  python3 scripts/install_global.py --status     # show current state
  python3 scripts/install_global.py --uninstall  # remove our links only
  python3 scripts/install_global.py --target ~/.cursor/skills  # extra dir
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_plugins import REPO_ROOT, find_skills  # noqa: E402

DEFAULT_TARGETS = [
    Path("~/.agents/skills"),
    Path("~/.claude/skills"),
]


def points_into_repo(link: Path) -> bool:
    try:
        target = Path(os.readlink(link))
    except OSError:
        return False
    if not target.is_absolute():
        target = link.parent / target
    try:
        target.resolve(strict=False).relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def plan(target_dir: Path, skills: dict[str, Path]) -> list[tuple[str, Path, Path | None]]:
    """Returns (action, link_path, source) tuples for one target directory.
    Actions: ok, create, update, remove-stale, conflict."""
    actions = []
    for name, source in skills.items():
        link = target_dir / name
        if link.is_symlink():
            if not points_into_repo(link):
                actions.append(("conflict", link, source))
            elif link.resolve() == source.resolve():
                actions.append(("ok", link, source))
            else:
                actions.append(("update", link, source))
        elif link.exists():
            actions.append(("conflict", link, source))
        else:
            actions.append(("create", link, source))

    # Links we created earlier for skills that were since renamed, removed,
    # or moved to deprecated/ / in-progress/.
    if target_dir.is_dir():
        for entry in sorted(target_dir.iterdir()):
            if entry.name not in skills and entry.is_symlink() and points_into_repo(entry):
                actions.append(("remove-stale", entry, None))
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print the plan without changing anything")
    mode.add_argument("--status", action="store_true", help="print the current state of every link")
    mode.add_argument("--uninstall", action="store_true", help="remove every symlink that points into this repo")
    parser.add_argument("--target", action="append", default=[], type=Path,
                        help="extra skills directory to install into (repeatable)")
    args = parser.parse_args()

    skills = {name: skill_dir for _, name, skill_dir in find_skills()}
    targets = [t.expanduser() for t in DEFAULT_TARGETS + args.target]
    dry = args.dry_run or args.status
    conflicts = 0

    for target_dir in targets:
        print(f"\n{target_dir}")
        if args.uninstall:
            entries = sorted(target_dir.iterdir()) if target_dir.is_dir() else []
            actions = [("remove", e, None) for e in entries if e.is_symlink() and points_into_repo(e)]
        else:
            actions = plan(target_dir, skills)

        for action, link, source in actions:
            if args.status and action == "create":
                action = "missing"
            shown = f" -> {source.relative_to(REPO_ROOT)}" if source else ""
            print(f"  {action:<13}{link.name}{shown}")
            if action == "conflict":
                conflicts += 1
            if dry or action in ("ok", "conflict", "missing"):
                continue
            if action in ("update", "remove", "remove-stale"):
                link.unlink()
            if action in ("create", "update"):
                target_dir.mkdir(parents=True, exist_ok=True)
                link.symlink_to(source, target_is_directory=True)

    if conflicts:
        print(f"\n{conflicts} conflict(s): a non-repo file or link already uses that name. "
              "Remove or rename it by hand, then re-run.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
