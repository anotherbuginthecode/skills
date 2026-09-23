---
name: project-board
description: Sets up issue organization for the current GitHub repository - explores the codebase to infer area labels (area:frontend, area:backend, area:ai, area:infra, ...), confirms the label set with the user, then creates the labels and a linked Projects v2 board (Todo -> In Progress -> In Review -> Needs human -> Done) with Board/Up next/My inbox/Supervised views. Invoked explicitly via /project-board, not triggered automatically.
disable-model-invocation: true
user-invocable: true
argument-hint: ""
---

# project-board

Sets up label-based issue organization and a Projects v2 board on the
**current, already-existing** GitHub repository - it does not create a repo
or scaffold process files (for that, use `/new-project`). Two kinds of work,
kept separate:

1. **Judgment** (you do this, in conversation): read the codebase, infer the
   area labels that reflect its real architecture, get the user's
   confirmation on the final label set.
2. **Execution** (a script does this, always the same way): create the
   labels and the board. Never hand-run individual `gh` commands for these
   steps - use `scripts/create_labels.sh` and
   `scripts/create_project_board.sh`. Small differences (missing `--force`
   on relabel, wrong owner on `gh project link`) are easy to get wrong by
   hand.

## Workflow

### 1. Confirm repo context

Run `gh repo view --json name,owner` from the current directory. If it
fails, the current directory isn't a GitHub repo (or `gh` isn't
authenticated) - tell the user and stop; don't guess a repo to target.

### 2. Explore the codebase for architecture

Read the repo's structure to find the real work domains, the same way you'd
orient yourself in an unfamiliar codebase - manifest files (`package.json`,
`pyproject.toml`, `requirements.txt`, `go.mod`, `Gemfile`, `*.csproj`), a
monorepo layout (`apps/*`, `packages/*`, `services/*`), infra signals
(`Dockerfile`, `docker-compose.yml`, `terraform/`, `k8s/`, `.github/workflows/`),
mobile signals (`ios/`, `android/`, `*.xcodeproj`, `build.gradle`), and
AI/LLM signals (`langchain`, `openai`, `anthropic`, `transformers` or similar
in dependencies). Use this to name the domains actually present (e.g.
`frontend`, `backend`, `ai`, `infra`, `mobile`, `data`) - not a fixed enum,
and not a label for a domain the codebase doesn't show evidence of.

Don't ask the user to pick from a fixed list of "modules" or "stacks" to
decide this - infer it from what's actually in the repo.

### 3. Propose labels

For each area you found evidence for, propose a label named
`area:<domain>` (e.g. `area:frontend`, `area:ai`):

- A one-line description of what it covers.
- A hex color you pick yourself, semantically if you can (e.g. red-adjacent
  for security-adjacent domains, blue for data-facing ones) - don't ask the
  user to choose colors, only to approve, drop, rename, or add labels.

Present the full proposed list to the user as a checklist (one item per
label, checked by default) so they can uncheck any they don't want, and
leave room for them to add labels you didn't infer. Don't create anything
until they've confirmed the final set.

### 4. Write the config file

Once the label set is settled, write a small JSON file (e.g. to your
scratchpad directory):

```json
{
  "labels": [
    {
      "name": "area:frontend",
      "color": "1D76DB",
      "description": "UI and client-side code"
    },
    {
      "name": "area:backend",
      "color": "0E8A16",
      "description": "Server-side application logic"
    },
    {
      "name": "area:ai",
      "color": "5319E7",
      "description": "Model integration and prompt logic"
    }
  ]
}
```

### 5. Create the labels and the board

From inside the repo's working tree, run:

```
scripts/create_labels.sh --config <path-to-config.json>
scripts/create_project_board.sh
```

`create_labels.sh` is idempotent - safe to re-run if the label set changes
later. `create_project_board.sh` is not - it always creates a new board, so
only run it once per repo; it reads the repo's own owner/name via `gh repo
view`, so it works whether the repo is personal or org-owned. It creates a
Projects v2 board with a `Status` field (Todo -> In Progress -> In Review ->
Needs human -> Done), links it to the repo, and sets up four views:

- **Board** - the default board view, grouped by status, showing
  Title/Assignees/Labels/Linked pull requests.
- **Up next** - table view filtered to `status:Todo`.
- **My inbox** - table view filtered to `status:"Needs human"`, for items
  that need a person's attention.
- **Supervised** - table view filtered to `label:"autonomy:supervised"`.

### 6. Report back

Tell the user which labels were created and give them the board link that
`create_project_board.sh` prints (from `gh project link`'s output / the
project number it reports).
