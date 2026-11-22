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
  "file": { "path": "~/dev-journal/journal.md" },
  "content_repo": "~/Desktop/workspace/ai/social-media-agents"
}
```

`destination` is `notion`, `file`, or `chat`. A `--to` argument overrides it for this run without changing the file.

`content_repo` is the folder that defines the user's content strategy. Content ideas are shaped by three files in it:

- `AGENT.md` - the audiences.
- `archivio/voce.md` - the formats, F1-F7, in section 10 ("Formats").
- `archivio/post-indice.md` - the allowed theme tags.

If the file is missing, ask the user once which destination to use (Notion, a local file with its path, or chat only), which language to write in, and where their content repo is. Default the language to the one the user writes their prompts in. Save the answers to the config file, then continue. Do not ask again on later runs.

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
- **Content ideas.** Post or blog seeds, written to the rules in "Content ideas" below.
- **Threads to explore.** Open questions and ideas that came up and were not pursued.
- **Retro answers.** One line for each question in "Retro questions" below.

### Content ideas

Before writing ideas, read `AGENT.md`, section 10 of `archivio/voce.md`, and the theme list in `archivio/post-indice.md` from `content_repo`. If `content_repo` is not set or a file is missing, say which one is missing. Then use the best match you can for audience, format, and themes, and mark those fields `(unchecked)`.

Keep only ideas that fit one of the two audiences in `AGENT.md`:

- Tech leads who are bringing coding agents into their team's real work.
- Founders who are building with AI-native teams.

If an idea fits only another audience, such as home lab users or platform engineers, list it in one line under "Other ideas".

Fill in every field for each idea:

- **Title:** a possible first line of 10 to 12 words. Include a number or a named thing if there is a real one.
- **What I want to say:** one or two sentences.
- **Why my audience cares:** what a tech lead or founder does differently after reading it.
- **Facts and data from today:** only things that were measured or observed: numbers, episodes, decisions. Give the source of each one (a file, test case, ADR, or session id).
- **Material:** screenshots, tables, outputs, or diagrams that could become the post's image, with their path or link.
- **What's missing:** what still has to be found out, decided, or measured before the post can be written. Write "Nothing" if the idea is ready.
- **Can it be public:** what can be shown and what must stay private, such as private repos, the home setup, client names, or terms of service.
- **Audience:** `tech-leads` or `founders`. Never both.
- **Format:** one of F1 to F7 from `archivio/voce.md`. Add `blog` if the idea needs more room than a post.
- **Themes:** two to four tags from the list in `archivio/post-indice.md`.

Do not invent facts to make an idea look ready. If there are no facts, the idea goes in with "What's missing" filled in, or it is dropped.

### Retro questions

Answer each question in one line, from today's sessions. If the sessions do not answer a question, write "-".

1. What broke?
2. What did I decide, and why?
3. What did I explain or ask more than once?
4. Which number surprised me?
5. What would I tell myself a month ago?

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
### <Title>
- What I want to say:
- Why my audience cares:
- Facts and data from today:
- Material:
- What's missing:
- Can it be public:
- Audience:
- Format:
- Themes:
### Other ideas
- <one line each>
## Retro questions
1. What broke?
2. What did I decide, and why?
3. What did I explain or ask more than once?
4. Which number surprised me?
5. What would I tell myself a month ago?
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
   - `Tags` (multi-select) - the themes used by the entry's content ideas, from `archivio/post-indice.md`
   - `Content status` (select: `Raw`, `Drafting`, `Published`) - new entries are `Raw`
   - `Ideas` (number) - how many content ideas the entry has, not counting "Other ideas"
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
