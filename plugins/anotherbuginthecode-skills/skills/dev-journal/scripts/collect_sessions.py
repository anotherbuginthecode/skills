#!/usr/bin/env python3
"""Condense Claude Code session transcripts into a compact Markdown digest.

Claude Code stores every session as JSONL under
~/.claude/projects/<encoded-cwd>/<session-id>.jsonl. Raw transcripts are huge
(tool output, system reminders, injected instructions), so this script keeps
only what a journal needs: the human's prompts, Claude's prose replies, a
one-line summary of each tool call, files touched, and commits made.

Usage:
  collect_sessions.py [--date YYYY-MM-DD] [--cwd PATH] [--session ID]
                      [--all-projects] [--max-chars N]

Defaults: today's local date, the current working directory's project,
every session that has activity on that date.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"

# Blocks the harness injects into user turns; they are not the human talking.
INJECTED_TAGS = re.compile(
    r"<(system-reminder|browser_instruction|command-message|command-args|"
    r"local-command-stdout|local-command-caveat|user-prompt-submit-hook|"
    r"ide_selection|ide_opened_file)[^>]*>.*?</\1>",
    re.DOTALL,
)
COMMAND_NAME = re.compile(r"<command-name>(.*?)</command-name>", re.DOTALL)

USER_LIMIT = 1500
ASSISTANT_LIMIT = 900


def encode_cwd(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def clip(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    half = limit // 2
    return f"{text[:half]} [...] {text[-half:]}"


def local_dt(ts: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except (ValueError, AttributeError):
        return None


def tool_summary(block: dict) -> tuple[str, str | None]:
    """Return (one-line summary, touched file path or None)."""
    name = block.get("name", "?")
    inp = block.get("input") or {}
    path = inp.get("file_path") or inp.get("notebook_path")
    if name in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        return f"{name} {path}", path
    if name == "Read":
        if path and str(PROJECTS_DIR) in path:
            return "Read (spilled tool output)", None
        return f"Read {path}", None
    if name == "Bash":
        desc = inp.get("description") or clip(inp.get("command", ""), 120)
        return f"Bash: {desc}", None
    if name in ("WebSearch", "WebFetch"):
        return f"{name}: {inp.get('query') or inp.get('url') or ''}", None
    if name in ("Agent", "Task"):
        return f"{name}: {inp.get('description', '')}", None
    if name == "Skill":
        return f"Skill: {inp.get('skill', '')} {inp.get('args', '')}".rstrip(), None
    if name in ("Grep", "Glob"):
        return f"{name}: {inp.get('pattern', '')}", None
    return name, None


def user_text(content) -> str:
    if isinstance(content, str):
        parts = [content]
    else:
        parts = [c.get("text", "") for c in content if c.get("type") == "text"]
    raw = "\n".join(parts)
    cmd = COMMAND_NAME.search(raw)
    cleaned = INJECTED_TAGS.sub("", COMMAND_NAME.sub("", raw)).strip()
    if cmd:
        cleaned = f"{cmd.group(1).strip()} {cleaned}".strip()
    return cleaned


def digest_session(path: Path, day: dt.date) -> dict | None:
    title = None
    cwd = branch = None
    events: list[str] = []
    files: set[str] = set()
    commits: list[str] = []
    first = last = None
    tool_count = 0

    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = d.get("type")
            if kind == "ai-title":
                title = d.get("aiTitle") or title
                continue
            if kind == "summary" and not title:
                title = d.get("summary")
                continue
            if kind not in ("user", "assistant") or d.get("isSidechain"):
                continue
            when = local_dt(d.get("timestamp", ""))
            if not when or when.date() != day:
                continue
            first = first or when
            last = when
            cwd = d.get("cwd") or cwd
            branch = d.get("gitBranch") or branch
            msg = d.get("message") or {}
            content = msg.get("content")
            stamp = when.strftime("%H:%M")

            if kind == "user":
                if d.get("isMeta") or d.get("isCompactSummary"):
                    continue
                if isinstance(content, list) and all(
                    c.get("type") == "tool_result" for c in content
                ):
                    continue
                text = user_text(content)
                if text:
                    events.append(f"\n**[{stamp}] USER:** {clip(text, USER_LIMIT)}")
                continue

            for block in content or []:
                btype = block.get("type")
                if btype == "text" and block.get("text", "").strip():
                    events.append(f"**[{stamp}] CLAUDE:** {clip(block['text'], ASSISTANT_LIMIT)}")
                elif btype == "tool_use":
                    tool_count += 1
                    summary, touched = tool_summary(block)
                    if touched:
                        files.add(touched)
                    cmd = (block.get("input") or {}).get("command", "")
                    if "git commit" in cmd:
                        m = re.search(r"-m\s+[\"'](.+?)[\"']", cmd) or re.search(
                            r"<<'?EOF'?\n(.+?)\n", cmd
                        )
                        commits.append(m.group(1) if m else "(commit)")
                    events.append(f"  - tool: {clip(summary, 200)}")

    if not events or first is None:
        return None
    return {
        "id": path.stem,
        "title": title or "(untitled)",
        "cwd": cwd,
        "branch": branch,
        "start": first,
        "end": last,
        "tools": tool_count,
        "files": sorted(files),
        "commits": commits,
        "events": events,
    }


def project_dirs(cwd: str, all_projects: bool) -> list[Path]:
    if not PROJECTS_DIR.exists():
        return []
    if all_projects:
        return sorted(p for p in PROJECTS_DIR.iterdir() if p.is_dir())
    exact = PROJECTS_DIR / encode_cwd(cwd)
    return [exact] if exact.is_dir() else []


def render(session: dict, budget: int) -> str:
    head = [
        f"## Session {session['id']} - {session['title']}",
        f"- Time: {session['start']:%H:%M} -> {session['end']:%H:%M}",
        f"- Folder: {session['cwd']} (branch: {session['branch']})",
        f"- Tool calls: {session['tools']}",
    ]
    if session["files"]:
        head.append("- Files changed: " + ", ".join(session["files"][:40]))
    if session["commits"]:
        head.append("- Commits: " + " | ".join(session["commits"]))
    head.append("\n### Conversation")
    body = "\n".join(session["events"])
    if len(body) > budget:
        # Keep the opening (the goal) and the end (the outcome).
        body = body[: budget * 2 // 5] + "\n\n[... middle of session trimmed ...]\n\n" + body[-budget * 3 // 5 :]
    return "\n".join(head) + "\n" + body + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", help="YYYY-MM-DD, local time (default: today)")
    ap.add_argument("--cwd", default=os.getcwd(), help="project folder (default: current directory)")
    ap.add_argument("--session", help="only this session id")
    ap.add_argument("--all-projects", action="store_true", help="every project folder, not just --cwd")
    ap.add_argument("--max-chars", type=int, default=120_000, help="total output budget")
    args = ap.parse_args()

    day = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    dirs = project_dirs(os.path.abspath(args.cwd), args.all_projects)
    if not dirs:
        print(f"No Claude Code sessions folder found for {args.cwd} under {PROJECTS_DIR}", file=sys.stderr)
        sys.exit(2)

    sessions = []
    for d in dirs:
        for f in d.glob("*.jsonl"):
            if args.session and f.stem != args.session:
                continue
            # Cheap pre-filter: a file last written before the day can't hold it.
            if dt.date.fromtimestamp(f.stat().st_mtime) < day:
                continue
            s = digest_session(f, day)
            if s:
                sessions.append(s)

    if not sessions:
        print(f"No session activity on {day} for the selected scope.", file=sys.stderr)
        sys.exit(3)

    sessions.sort(key=lambda s: s["start"])
    budget = max(4_000, args.max_chars // len(sessions))
    print(f"# Claude Code sessions digest - {day}\n")
    print(f"Sessions: {len(sessions)} | Projects: {', '.join(sorted({s['cwd'] or '?' for s in sessions}))}\n")
    for s in sessions:
        print(render(s, budget))


if __name__ == "__main__":
    main()
