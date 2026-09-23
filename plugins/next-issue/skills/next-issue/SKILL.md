---
name: next-issue
description: "Coordinates one iteration of the delivery loop: resumes or picks the next ready GitHub issue for an area, delivers it through /task-to-pr, applies the board's autonomy rules, and ends with a LOOP_STATUS line. Use to drive implementation one issue per fresh context."
user-invocable: true
argument-hint: "<area: infra|backend|frontend|security|docs>"
---

# Next issue

Coordinate exactly one issue. Invoking this skill by name grants merge authority for `autonomy:auto` issues, as /task-to-pr requires. Never start a second issue. Follow "Board conventions" in AGENTS.md.

## 1. Preflight

- Be on main with a clean tree, then `git pull --ff-only`. Otherwise end with BLOCKED.
- If the latest CI run on main failed, end with BLOCKED ("main is red").

## 2. Resume or select

- Resume first: an issue labeled `area:<area>`, In Progress or In Review, without `needs-human`. Continue it from its branch and PR.
- Otherwise pick the lowest-numbered Todo issue labeled `area:<area>` whose "Depends on" issues are all Done. If none, end with EMPTY.
- `autonomy:supervised` with no comment from the repository owner starting with "Approved": post the plan as an issue comment, add `needs-human`, set status Needs human, end with NEEDS_HUMAN.
- Move the issue to In Progress.

## 3. Deliver

Run /task-to-pr for this single issue from the latest main. Dependencies are merged, so never stack.

## 4. Stop rules

- Missing product or technical decision, or /review verdict Blocked: comment the problem, options, and your recommendation; add `needs-human`; set Needs human; end with NEEDS_HUMAN.
- /test Fail or blocked, /review Request changes after two fix cycles, or CI red after two fixes: comment the blocker; add `needs-human`; set Needs human; end with BLOCKED. Never merge.
- `autonomy:supervised` after an Approve verdict and green CI: comment "Ready to merge" with the proof; add `needs-human`; set Needs human; end with NEEDS_HUMAN. Do not merge.

## 5. Finish an auto issue

- Squash-merge after an Approve verdict and green CI. Wait until GitHub reports it merged and check the PR says `Closes #N`.
- A mistake that happened twice becomes a CLAUDE.md "Gotchas" line. A new hard-to-reverse decision becomes an ADR.

## 6. Report

Issue · PR · /test result · /review verdict and findings fixed/declined · CI · next ready issue.
The last line is exactly one of:
LOOP_STATUS: DONE | LOOP_STATUS: EMPTY | LOOP_STATUS: NEEDS_HUMAN | LOOP_STATUS: BLOCKED
