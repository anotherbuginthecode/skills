#!/usr/bin/env bash
# Copy and render the repo's process files into the current directory.
# Must run from inside the target repo's working tree (after create_repo.sh).
# Usage: scaffold_files.sh --config <project-config.json>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$SCRIPT_DIR/../assets"

CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  echo "Usage: scaffold_files.sh --config <project-config.json>" >&2
  exit 1
fi

PROJECT_NAME=$(jq -r '.repo_name' "$CONFIG")
PROJECT_DESCRIPTION=$(jq -r '.project_description' "$CONFIG")
AREA_LABELS=$(jq -r '.area_labels | join("|")' "$CONFIG")
REVIEW_SKILL=$(jq -r '.workflow_skills.review.name' "$CONFIG")
TASK_TO_PR_ENABLED=$(jq -r '.workflow_skills.task_to_pr.enabled' "$CONFIG")
TASK_TO_PR_SKILL=$(jq -r '.workflow_skills.task_to_pr.name // ""' "$CONFIG")

mkdir -p .github/ISSUE_TEMPLATE .claude

cp "$ASSETS_DIR/gitignore" .gitignore
cp "$ASSETS_DIR/ISSUE_TEMPLATE/task.md" .github/ISSUE_TEMPLATE/task.md
cp "$ASSETS_DIR/settings.json.template" .claude/settings.json

python3 "$SCRIPT_DIR/render_template.py" "$ASSETS_DIR/AGENTS.md.template" AGENTS.md \
  "PROJECT_NAME=$PROJECT_NAME" "PROJECT_DESCRIPTION=$PROJECT_DESCRIPTION" "AREA_LABELS=$AREA_LABELS" \
  "REVIEW_SKILL=$REVIEW_SKILL" "TASK_TO_PR=$TASK_TO_PR_ENABLED" "TASK_TO_PR_SKILL=$TASK_TO_PR_SKILL"

python3 "$SCRIPT_DIR/render_template.py" "$ASSETS_DIR/pull_request_template.md.template" .github/pull_request_template.md \
  "REVIEW_SKILL=$REVIEW_SKILL"

python3 "$SCRIPT_DIR/render_template.py" "$ASSETS_DIR/PRODUCT.md.template" PRODUCT.md \
  "PROJECT_NAME=$PROJECT_NAME"

echo "Scaffolded .gitignore, issue/PR templates, .claude/settings.json, AGENTS.md, PRODUCT.md."
