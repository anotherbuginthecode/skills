#!/usr/bin/env bash
# Create the remote GitHub repo and clone it locally.
# Usage: create_repo.sh --config <project-config.json>
set -euo pipefail

CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  echo "Usage: create_repo.sh --config <project-config.json>" >&2
  exit 1
fi

REPO_NAME=$(jq -r '.repo_name' "$CONFIG")
VISIBILITY=$(jq -r '.visibility' "$CONFIG")
DESCRIPTION=$(jq -r '.description' "$CONFIG")

if [[ -z "$REPO_NAME" || "$REPO_NAME" == "null" ]]; then
  echo "repo_name missing in config" >&2
  exit 1
fi

if [[ "$VISIBILITY" != "private" && "$VISIBILITY" != "public" && "$VISIBILITY" != "internal" ]]; then
  echo "visibility must be private, public, or internal (got: $VISIBILITY)" >&2
  exit 1
fi

gh repo create "$REPO_NAME" "--${VISIBILITY}" --description "$DESCRIPTION" --clone

echo "Created and cloned ${REPO_NAME} (${VISIBILITY})."
