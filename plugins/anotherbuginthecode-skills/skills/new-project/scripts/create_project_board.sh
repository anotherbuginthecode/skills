#!/usr/bin/env bash
# Create a GitHub Projects v2 board with a Status field
# (Todo -> In Progress -> In Review -> Done) and link it to the repo.
# Usage: create_project_board.sh --config <project-config.json>
set -euo pipefail

CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  echo "Usage: create_project_board.sh --config <project-config.json>" >&2
  exit 1
fi

REPO_NAME=$(jq -r '.repo_name' "$CONFIG")
# gh project link rejects "@me" as owner (owner must match the repo's literal
# login), so resolve the real login once and reuse it everywhere below.
OWNER=$(gh api user --jq .login)

PROJECT_JSON=$(gh project create --owner "$OWNER" --title "$REPO_NAME" --format json)
PROJECT_NUMBER=$(jq -r '.number' <<<"$PROJECT_JSON")

FIELDS_JSON=$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json)
STATUS_FIELD_ID=$(jq -r '.fields[] | select(.name == "Status") | .id' <<<"$FIELDS_JSON")
TODO_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Todo") | .id' <<<"$FIELDS_JSON")
IN_PROGRESS_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "In Progress") | .id' <<<"$FIELDS_JSON")
DONE_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Done") | .id' <<<"$FIELDS_JSON")

if [[ -z "$STATUS_FIELD_ID" || "$STATUS_FIELD_ID" == "null" ]]; then
  echo "Could not find the default Status field on project #${PROJECT_NUMBER}" >&2
  exit 1
fi

# updateProjectV2Field replaces the whole option list, so existing options
# are passed back with their original ids (to preserve them) alongside the
# new "In Review" option (left without an id so GitHub assigns one).
gh api graphql -f query='
mutation($fieldId: ID!, $todoId: String!, $inProgressId: String!, $doneId: String!) {
  updateProjectV2Field(input: {
    fieldId: $fieldId,
    singleSelectOptions: [
      { id: $todoId, name: "Todo", color: GRAY, description: "" },
      { id: $inProgressId, name: "In Progress", color: YELLOW, description: "" },
      { name: "In Review", color: BLUE, description: "" },
      { id: $doneId, name: "Done", color: GREEN, description: "" }
    ]
  }) {
    projectV2Field {
      ... on ProjectV2SingleSelectField { id }
    }
  }
}' -f fieldId="$STATUS_FIELD_ID" -f todoId="$TODO_ID" -f inProgressId="$IN_PROGRESS_ID" -f doneId="$DONE_ID" >/dev/null

gh project link "$PROJECT_NUMBER" --owner "$OWNER" --repo "${OWNER}/${REPO_NAME}"

echo "Project board #${PROJECT_NUMBER} ready (Todo -> In Progress -> In Review -> Done), linked to ${OWNER}/${REPO_NAME}."
