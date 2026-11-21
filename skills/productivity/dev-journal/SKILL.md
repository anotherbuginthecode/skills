---
name: dev-journal
description: Turns today's Claude Code sessions in the current folder (or one session, a past day, or every project) into a dev-journal entry - what was sought, what was achieved, what was learned, dead ends, and ideas for posts, blogs, and further exploration - and saves it to Notion, a local .md/.txt file, or the chat. Invoked explicitly via /dev-journal, not triggered automatically.
disable-model-invocation: true
user-invocable: true
argument-hint: "[today|session|YYYY-MM-DD] [--to notion|file:<path>|chat] [--all-projects]"
---

# Dev journal

Read the user's Claude Code sessions and write one journal entry for the day. The entry is raw material for later: posts, blog articles, talks, and ideas to explore. It is not a timesheet.

## 1. Parse arguments

| Argument | Meaning | Default |
| --- | --- | --- |
| `today` | Every session with activity today in the current folder | yes |
| `session` | Only the current session. Its id is the newest `.jsonl` in the project folder, or the one the user names | |
| `YYYY-MM-DD` | Every session with activity on that local date | |
| `--all-projects` | Every project folder, not just the current one | off |
| `--to notion` / `--to file:<path>` / `--to chat` | Destination for this run only | from config |

Free text after the arguments is a focus hint, for example "focus on the AI evaluation work". Use it to weigh what goes in the entry.

## 2. Load the destination

Read `~/.claude/dev-journal/config.json`. Shape:

```json
{
  "destination": "notion",
  "language": "it",
  "notion": { "database_id": "...", "data_source_id": "...", "url": "..." },
  "file": { "path": "~/dev-journal/journal.md" }
}
```

`destination` is `notion`, `file`, or `chat`. A `--to` argument overrides it for this run without changing the file.

If the file is missing, ask the user once which destination to use (Notion, a local file with its path, or chat only) and which language to write in. Default the language to the one the user writes their prompts in. Save the answer to the config file, then continue. Do not ask again on later runs.

## 3. Collect the sessions

Run the bundled script. It strips injected system text and tool output and keeps prompts, replies, tool-call summaries, changed files, and commits.

```bash
python3 "<this skill's directory>/scripts/collect_sessions.py" --cwd "$PWD" [--date YYYY-MM-DD] [--session ID] [--all-projects]
```

- Exit code 3 means no activity in that scope. Say so and stop. Suggest `--all-projects` or another date if that would help.
- Exit code 2 means no sessions folder exists for this directory. Suggest `--all-projects`.
- The output is capped near 120k characters. Long sessions keep their opening and their end, where the goal and the outcome live. If a trimmed session looks central to the day, re-run with `--session <id> --max-chars 60000` to read it in full.

The current session is included. Ignore the turn that invoked this skill and everything after it.

## 4. Analyze

Read the digest as a senior engineer and writer would read a colleague's lab notebook. Separate what happened from what is worth telling.

Extract:

- **Goals.** What the user was trying to find out or build, in their own terms. Merge goals that recur across sessions.
- **Outcomes.** What exists now that did not exist this morning: code, decisions, documents, commits, answers. Be concrete and name files, tools, and numbers.
- **Learnings.** Things that were non-obvious: a surprising tool behavior, a wrong assumption corrected, a technique that worked, a trade-off settled. Learnings are the most valuable part. Prefer a sharp specific fact to a general lesson.
- **Dead ends and friction.** Approaches that failed and why, places where the AI misunderstood, time sinks. These often make the best post material.
- **How the AI was used.** Delegation patterns, prompts or skills that worked, places where the human had to steer. This is a recurring theme for the user's content.
- **Content ideas.** Two to five post or blog seeds. Each needs a hook (one line a reader would stop for), an angle (why this view is not generic), an audience, a format (LinkedIn post, thread, blog article, talk, demo), and the evidence from today that backs it.
- **Threads to explore.** Open questions and ideas that came up and were not pursued.

Rules:

- Write only what the digest supports. Do not invent results, numbers, or motivations. If an outcome is unclear, say it is unclear.
- Skip mechanical work such as listing files or installing dependencies unless it taught something.
- Never copy secrets, tokens, credentials, customer data, or personal data of third parties into the entry. Describe them generically.
- Write in the configured language. Keep code identifiers and commands as they are.

## 5. Write the entry

Use this structure. Omit a section only when it would be empty.

```markdown
# <YYYY-MM-DD> - <short headline for the day>

**TL;DR:** <two or three sentences>

## What I was after
## What I got
## What I learned
## Dead ends and friction
## How I worked with AI
## Content ideas
### <Hook>
- Angle:
- Audience:
- Format:
- Evidence from today:
## Threads to explore
## Sessions
- <HH:MM-HH:MM> <title> - <project folder> - `<session id>`
```

Translate the headings into the configured language.

## 6. Save

An entry is unique per date and project. With `--all-projects`, the project is `all`. Before writing, look for an existing entry with the same key. If one exists, merge into it: keep what is there, add what is new, and update the TL;DR and session list. Do not create a duplicate.

### Notion

Use the Notion MCP tools. If they are not connected, tell the user to connect the Notion connector, then fall back to `chat` for this run.

1. If the config has no `notion.database_id`, search Notion for a database named "Dev Journal". If none exists, create it as a private page (or under a parent page the user names) with these properties:
   - `Name` (title)
   - `Date` (date)
   - `Project` (select) - the project folder's basename, or `all`
   - `Tags` (multi-select) - 3 to 6 topical tags, such as `claude-code`, `agents`, `rag`, `aws`
   - `Content status` (select: `Raw`, `Drafting`, `Published`) - new entries are `Raw`
   - `Ideas` (number) - how many content ideas the entry has
   - `Sessions` (number)

   Save the database and data source ids and the URL to the config.
2. Query the database for a row with the same `Date` and `Project`. Update it if one exists. Otherwise create a page with the properties above and the entry body as content.
3. Reply with the page link.

### File

Expand `~` in the configured path. Create parent folders if needed.

- `.md`: append the entry as Markdown. If a heading for the same date and project already exists, replace that section with the merged entry.
- `.txt` or any other extension: write the same content as plain text. Use underlined headings (`====` and `----`) and `-` bullets, with no Markdown syntax.
- If the path is a directory, write one file per day: `<dir>/<YYYY-MM-DD>-<project>.md`.

Reply with the file path.

### Chat

Print the entry in the reply. Do not write anything to disk.

## 7. Report

End with three lines at most: where the entry went, how many sessions it covers, and the strongest content idea. Do not repeat the whole entry unless the destination is `chat`.
