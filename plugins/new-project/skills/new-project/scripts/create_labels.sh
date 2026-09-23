#!/usr/bin/env bash
# Create (or update) every label listed in the config on the repo in the
# current directory. Idempotent: safe to re-run.
# Usage: create_labels.sh --config <project-config.json>
set -euo pipefail

CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  echo "Usage: create_labels.sh --config <project-config.json>" >&2
  exit 1
fi

jq -c '.labels[]' "$CONFIG" | while read -r label; do
  name=$(jq -r '.name' <<<"$label")
  color=$(jq -r '.color' <<<"$label")
  description=$(jq -r '.description' <<<"$label")
  gh label create "$name" --color "$color" --description "$description" --force
  echo "Label ready: $name"
done
