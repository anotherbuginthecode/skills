---
name: new-project
description: Bootstraps a new GitHub repository with the process structure this user's projects use to be managed autonomously by AI agents - .gitignore, issue/PR templates, AGENTS.md policy, PRODUCT.md skeleton, GitHub labels, a Projects v2 board, and committed .claude/settings.json. Use whenever the user asks to start a new project, bootstrap a new repo, set up a new GitHub project for agent-driven development, or scaffold the standard engineering process files for a repo. Trigger even if they only describe the project idea without naming these files explicitly - inferring what the repo needs is part of the job.
---

# new-project

Bootstraps a new GitHub repository so it can be run autonomously by AI
agents from day one: a fixed set of process files, a label taxonomy that
reflects the project's real work domains, and a Projects v2 board with the
standard status flow.

Two kinds of work happen here, and they must not blend together:

1. **Judgment** (you do this, in conversation): understand what the user is
   building, propose the labels and text that should reflect it, get their
   confirmation.
2. **Execution** (a script does this, always the same way): create the
   repo, write the files, create the labels, create the board, commit,
   push. Never hand-run individual `gh`/`git` commands for these steps -
   use `scripts/bootstrap.sh`. It has been tested end to end; ad hoc
   commands have not, and small differences (missing `--force` on relabel,
   forgetting to set push upstream, wrong owner on `gh project link`) are
   easy to get wrong by hand.

## Workflow

### 1. Interview

Ask (conversationally, not necessarily as a rigid form) for whatever of
this you don't already have from context:

- Repo name (required).
- A one- or two-sentence description of what the project does. This
  description does two jobs: it becomes the repo description and the
  opening line of `AGENTS.md`, and it's what you use in step 2 to infer
  labels.
- Visibility: default to `private` unless the user says otherwise.

Do not ask the user to pick from a fixed list of "modules" or "stacks" to
decide area labels or `.gitignore` contents - that conflates tech stack
with work domain (a chatbot feature can live entirely in a backend
repo; "infra" can mean repo restructuring, not just provisioning).
`.gitignore` here is deliberately stack-agnostic (see step 4); area labels
come from step 2 instead.

### 2. Propose labels

Always include these labels, verbatim (name, color, description) - they
are cross-cutting and don't depend on the project:

| name                  | color    | description                            |
| --------------------- | -------- | -------------------------------------- |
| `docs`                | `0075CA` | Documentation                          |
| `security`            | `D93F0B` | Security-sensitive                     |
| `autonomy:auto`       | `C2E0C6` | Agent delivers end to end              |
| `autonomy:supervised` | `FBCA04` | Needs human approval before/after code |
| `needs-human`         | `E11D21` | Runtime signal: human must act now     |

Beyond those, read the project description and propose additional area
labels for the real work domains you can infer (e.g. `payments`, `ai`,
`infra`, `frontend`, `backend`, `mobile` - whatever actually fits this
project, not a fixed enum). For each one you propose:

- Give it a one-line description of what it covers.
- Pick a hex color yourself, semantically if you can (e.g. red-adjacent
  for security-adjacent domains, blue for data-facing ones) - do not ask
  the user to choose colors, only to approve or edit the label set itself.

Show the full proposed list (fixed + inferred) to the user and get their
go-ahead before creating anything. They may add, remove, or rename
entries - the final, approved list is what goes in the config file in
step 3.

### 3. Write the config file

Once the name, description, visibility, and label list are settled, write
a single JSON file (e.g. to your scratchpad directory) that every script
below reads. This is the handoff point from judgment to execution - after
this file is written, nothing in the remaining steps requires further
inference.

```json
{
  "repo_name": "my-project",
  "visibility": "private",
  "description": "Short one-line repo description.",
  "project_description": "Same or slightly longer description, used as the opening line of AGENTS.md.",
  "area_labels": ["docs", "security", "payments"],
  "labels": [
    { "name": "docs", "color": "0075CA", "description": "Documentation" },
    {
      "name": "security",
      "color": "D93F0B",
      "description": "Security-sensitive"
    },
    {
      "name": "payments",
      "color": "5319E7",
      "description": "Billing and payment processing"
    },
    {
      "name": "autonomy:auto",
      "color": "C2E0C6",
      "description": "Agent delivers end to end"
    },
    {
      "name": "autonomy:supervised",
      "color": "FBCA04",
      "description": "Needs human approval before/after code"
    },
    {
      "name": "needs-human",
      "color": "E11D21",
      "description": "Runtime signal: human must act now"
    }
  ]
}
```

Notes:

- `area_labels` is the subset of label names (by convention, everything
  except the `autonomy:*` and `needs-human` ones) that appears in
  `AGENTS.md`'s "every issue has exactly one area label (...)" line. Order
  matters only for how that line reads.
- `labels` is the full list that gets created via `gh label create`.

### 4. Run the bootstrap

From the directory where you want the new repo cloned, run:

```
scripts/bootstrap.sh --config <path-to-config.json>
```

This single script (idempotent for labels, not for repo/board creation -
it always creates a new repo and a new board, so don't re-run it for the
same project) does, in order:

1. `gh repo create` + clone (`create_repo.sh`)
2. Copies `.gitignore` (fixed block only - see `assets/gitignore`), the
   issue and PR templates, `.claude/settings.json`, and renders
   `AGENTS.md` / `PRODUCT.md` from their templates (`scaffold_files.sh`)
3. Creates every label in the config (`create_labels.sh`)
4. Creates a Projects v2 board with a `Status` field
   (Todo → In Progress → In Review → Done) and links it to the repo
   (`create_project_board.sh`)
5. Generates `SETUP.md` from `references/default-skills.json`
   (`generate_setup_md.py`)
6. Commits everything and pushes

If you need to debug or re-run a single step (e.g. labels changed after
review), the individual scripts in `scripts/` all take the same
`--config` flag and can be run independently from inside the repo's
working tree.

### 5. Return SETUP.md to the user

`bootstrap.sh` prints `SETUP.md`'s contents at the end - a one-time,
per-machine Claude Code plugin marketplace setup (`/plugin marketplace
add ...`, `/plugin install ...@...`) for the skills this repo's
`AGENTS.md` and templates assume are installed (currently `review` and
`task-to-pr`, from `references/default-skills.json`).

This is not a side note to bury in a longer message: echo it back to the
user as the final, explicit output of the skill, since it's the one step
they still have to do by hand (marketplace registration can't be
committed to the repo - see `references/default-skills.md` maintenance
note below).

## Maintaining this skill over time

`references/default-skills.json` is the single source of truth for which
skills `SETUP.md` recommends installing. When you (or the user) build a
new skill worth using across projects - most likely under
`skills/engineering/` in this same marketplace repo - add an entry here:

```json
{
  "slug": "<skill-name>",
  "marketplace": "anotherbuginthecode/skills",
  "why": "<one line: what it does and why this repo's workflow needs it>"
}
```

No other change is needed; `generate_setup_md.py` picks it up
automatically on the next bootstrap.
