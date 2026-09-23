#!/usr/bin/env bash
# Orchestrates the full new-project bootstrap: create repo, scaffold process
# files, create labels, create the project board, generate SETUP.md, commit,
# push. Every step is deterministic; the caller is responsible for having
# already decided repo_name/description/labels/area_labels (agent judgment,
# confirmed with the user) before writing the config file this script reads.
#
# Usage: bootstrap.sh --config <project-config.json>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  echo "Usage: bootstrap.sh --config <project-config.json>" >&2
  exit 1
fi

# Resolve to an absolute path before we cd into the new repo directory below.
CONFIG="$(cd "$(dirname "$CONFIG")" && pwd)/$(basename "$CONFIG")"
REPO_NAME=$(jq -r '.repo_name' "$CONFIG")

echo "== 1/6 Creating repo =="
"$SCRIPT_DIR/create_repo.sh" --config "$CONFIG"

cd "$REPO_NAME"

echo "== 2/6 Scaffolding process files =="
"$SCRIPT_DIR/scaffold_files.sh" --config "$CONFIG"

echo "== 3/6 Creating labels =="
"$SCRIPT_DIR/create_labels.sh" --config "$CONFIG"

echo "== 4/6 Creating project board =="
"$SCRIPT_DIR/create_project_board.sh" --config "$CONFIG"

echo "== 5/6 Generating SETUP.md =="
python3 "$SCRIPT_DIR/generate_setup_md.py" "$SCRIPT_DIR/../references/default-skills.json" SETUP.md

echo "== 6/6 Committing and pushing =="
git add .
git commit -m "chore: bootstrap repository process files"
git push --set-upstream origin HEAD

echo ""
echo "Done. Repo: $(gh repo view --json url -q .url)"
echo ""
echo "--- SETUP.md (return this to the user as the skill's final step) ---"
cat SETUP.md
