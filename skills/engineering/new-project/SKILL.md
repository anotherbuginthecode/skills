---
name: new-project
description: Bootstraps a new GitHub repository with the process structure this user's projects use to be managed autonomously by AI agents - .gitignore, issue/PR templates, AGENTS.md policy, PRODUCT.md skeleton, GitHub labels, a Projects v2 board, and committed .claude/settings.json. Invoked explicitly via /new-project, not triggered automatically.
disable-model-invocation: true
user-invocable: true
argument-hint: "[repo name, short project description]"
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
- Technology or framework (optional): only ask if the description didn't
  already make it clear (e.g. "a Next.js e-commerce site" already
  answers this - don't ask again). Free text, not a pick-list - fold the
  answer into the project description you carry into the later steps. It
  doesn't drive `.gitignore` or area labels (see below), it's just
  useful context for whatever agent works in the repo afterward, and can
  sharpen your own label proposals in step 2.
- Visibility: default to `private` unless the user says otherwise.

Do not ask the user to pick from a fixed list of "modules" or "stacks" to
decide area labels or `.gitignore` contents - that conflates tech stack
with work domain (a chatbot feature can live entirely in a backend
repo; "infra" can mean repo restructuring, not just provisioning).
`.gitignore` here is deliberately stack-agnostic (see step 4); area labels
come from step 2 instead.

### 1.5. Explain the workflow, then settle the workflow skills

Explain briefly what the generated `AGENTS.md` will assume: a **code
review** skill gates every merge (referenced in Board conventions), and
an optional **task-to-pr** skill (referenced in its own "Workflow for
code changes" section) takes a task from an issue through a tested,
reviewed pull request. The user does not need to have either skill
installed yet - you're recording what the repo will assume, not
installing anything here.

Read `references/default-skills.json` for the suggested default for each
role and show it to the user, then ask:

- **Code review** (always required - `AGENTS.md`'s Board conventions
  always names one): use the default (`review`, from the
  `anotherbuginthecode/skills` marketplace), or a different skill? If
  different, ask for its name and where it comes from.
- **Task to PR** (optional): do they want this section in `AGENTS.md` at
  all? If yes, same question - default (`task-to-pr`, same marketplace)
  or a different skill, name and source.

For any skill - default or custom - get its source, since `SETUP.md`
(step 5) needs to know how to tell the user to get it:

- **marketplace**: a plugin marketplace (`owner/repo`, e.g.
  `anotherbuginthecode/skills`) - `SETUP.md` gets a `/plugin marketplace
  add` + `/plugin install` step.
- **npx**: installed by running an npx package - `SETUP.md` gets the
  `npx <package>` command.
- **local**: already lives in this project's own `skills/` folder -
  `SETUP.md` just notes it's already there, no install step.
- **global**: assumed already installed globally on the user's machine -
  `SETUP.md` just notes that assumption, no install step.

Don't guess the source for a skill you don't recognize - ask.

### 2. Propose labels

Always include these labels, verbatim (name, color, description) - they
are cross-cutting and don't depend on the project. `area:docs` and
`area:security` are area labels like any other (see below), just always
present regardless of what the project turns out to be:

| name                  | color    | description                            |
| --------------------- | -------- | -------------------------------------- |
| `area:docs`           | `0075CA` | Documentation                          |
| `area:security`       | `D93F0B` | Security-sensitive                     |
| `autonomy:auto`       | `C2E0C6` | Agent delivers end to end              |
| `autonomy:supervised` | `FBCA04` | Needs human approval before/after code |
| `needs-human`         | `E11D21` | Runtime signal: human must act now     |

Beyond those, read the project description and propose additional area
labels for the real work domains you can infer (e.g. `area:payments`,
`area:ai`, `area:infra`, `area:frontend`, `area:backend`, `area:mobile` -
whatever actually fits this project, not a fixed enum). Every area label
follows the `area:<domain>` naming convention - only `autonomy:*` and
`needs-human` fall outside it. For each one you propose:

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
  "area_labels": ["area:docs", "area:security", "area:payments"],
  "labels": [
    {
      "name": "area:docs",
      "color": "0075CA",
      "description": "Documentation"
    },
    {
      "name": "area:security",
      "color": "D93F0B",
      "description": "Security-sensitive"
    },
    {
      "name": "area:payments",
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
  ],
  "workflow_skills": {
    "review": {
      "name": "review",
      "why": "Runs the /review verdict referenced in AGENTS.md board conventions and the pull request template.",
      "source": { "type": "marketplace", "marketplace": "anotherbuginthecode/skills" }
    },
    "task_to_pr": {
      "enabled": true,
      "name": "task-to-pr",
      "why": "Takes a task from an issue through a tested, reviewed pull request; referenced by AGENTS.md's Workflow for code changes section.",
      "source": { "type": "marketplace", "marketplace": "anotherbuginthecode/skills" }
    }
  }
}
```

Notes:

- `area_labels` is the subset of label names (by convention, everything
  except the `autonomy:*` and `needs-human` ones) that appears in
  `AGENTS.md`'s "every issue has exactly one area label (...)" line. Order
  matters only for how that line reads.
- `labels` is the full list that gets created via `gh label create`.
- `workflow_skills` comes from step 1.5. `review` is always present.
  `task_to_pr.enabled: false` (or omitting `task_to_pr` entirely) drops
  the whole "Workflow for code changes" section from `AGENTS.md` and its
  entry from `SETUP.md` - `name`/`why`/`source` aren't needed in that
  case. `source.type` is `marketplace` (needs `marketplace`), `npx`
  (needs `package`), `local`, or `global` (neither needs more fields) -
  see step 1.5 for what each means.

### 4. Run the bootstrap

From the directory where you want the new repo cloned, run:

```
scripts/bootstrap.sh --config <path-to-config.json>
```

This single script (idempotent for labels, not for repo/board creation -
it always creates a new repo and a new board, so don't re-run it for the
same project) does, in order:

1. `gh repo create` + clone (`create_repo.sh`)
2. Copies `.gitignore` (fixed block only - see `assets/gitignore`) and the
   issue template, and renders `AGENTS.md`, the PR template, `PRODUCT.md`,
   and `.claude/settings.json` from their templates (`scaffold_files.sh`) -
   `AGENTS.md` and the PR template are rendered with the `workflow_skills`
   values from the config, including whether the "Workflow for code
   changes" section appears at all
3. Creates every label in the config (`create_labels.sh`)
4. Creates a Projects v2 board with a `Status` field
   (Todo → In Progress → In Review → Done) and links it to the repo
   (`create_project_board.sh`)
5. Generates `SETUP.md` from the config's `workflow_skills`
   (`generate_setup_md.py`)
6. Commits everything and pushes

If you need to debug or re-run a single step (e.g. labels changed after
review), the individual scripts in `scripts/` all take the same
`--config` flag and can be run independently from inside the repo's
working tree.

### 5. Return SETUP.md to the user

`bootstrap.sh` prints `SETUP.md`'s contents at the end - how to get each
workflow skill settled in step 1.5, exactly the way its `source` said to
(marketplace install command, npx command, or a note that it's already
local/global and needs nothing).

This is not a side note to bury in a longer message: echo it back to the
user as the final, explicit output of the skill, since for a
marketplace-sourced skill it's the one step they still have to do by hand
(marketplace registration can't be committed to the repo).

## Maintaining this skill over time

`references/default-skills.json` holds the suggested default for each
workflow role (`review`, `task_to_pr`) - what you offer the user in step
1.5 before asking if they'd rather use something else. It is not read by
any script; `generate_setup_md.py` and the `AGENTS.md`/PR template
rendering work entirely from the `workflow_skills` the user actually
settled on in the config file. When you (or the user) build a new skill
worth defaulting to for one of these roles - most likely under
`skills/engineering/` in this same marketplace repo - update its entry
here:

```json
{
  "review": {
    "name": "<skill-name>",
    "why": "<one line: what it does and why this repo's workflow needs it>",
    "source": { "type": "marketplace", "marketplace": "anotherbuginthecode/skills" }
  }
}
```

If a third workflow role becomes worth having a default for, add it as a
new top-level key here and give it the same treatment as `review` /
`task_to_pr` in step 1.5, the config schema, and `generate_setup_md.py`.
