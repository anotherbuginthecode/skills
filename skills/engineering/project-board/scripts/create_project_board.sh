#!/usr/bin/env bash
# Create a GitHub Projects v2 board with a Status field
# (Todo -> In Progress -> In Review -> Done) and link it to the repo in the
# current directory. Owner/repo are read from the repo itself, so this works
# whether the repo is personal or org-owned.
# Usage: create_project_board.sh
set -euo pipefail

REPO_JSON=$(gh repo view --json name,owner)
REPO_NAME=$(jq -r '.name' <<<"$REPO_JSON")
OWNER=$(jq -r '.owner.login' <<<"$REPO_JSON")

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
