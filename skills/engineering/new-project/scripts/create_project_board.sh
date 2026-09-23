#!/usr/bin/env bash
# Create a GitHub Projects v2 board matching the reference board layout:
# Status: Todo -> In Progress -> In Review -> Needs human -> Done, plus four
# views (Board, Up next, My inbox, Supervised). Links the board to the repo.
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
PROJECT_ID=$(jq -r '.id' <<<"$PROJECT_JSON")

FIELDS_JSON=$(gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json)
STATUS_FIELD_ID=$(jq -r '.fields[] | select(.name == "Status") | .id' <<<"$FIELDS_JSON")
TODO_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Todo") | .id' <<<"$FIELDS_JSON")
IN_PROGRESS_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "In Progress") | .id' <<<"$FIELDS_JSON")
DONE_ID=$(jq -r '.fields[] | select(.name == "Status") | .options[] | select(.name == "Done") | .id' <<<"$FIELDS_JSON")

if [[ -z "$STATUS_FIELD_ID" || "$STATUS_FIELD_ID" == "null" ]]; then
  echo "Could not find the default Status field on project #${PROJECT_NUMBER}" >&2
  exit 1
fi

TITLE_ID=$(jq -r '.fields[] | select(.name == "Title") | .id' <<<"$FIELDS_JSON")
ASSIGNEES_ID=$(jq -r '.fields[] | select(.name == "Assignees") | .id' <<<"$FIELDS_JSON")
LABELS_ID=$(jq -r '.fields[] | select(.name == "Labels") | .id' <<<"$FIELDS_JSON")
LINKED_PRS_ID=$(jq -r '.fields[] | select(.name == "Linked pull requests") | .id' <<<"$FIELDS_JSON")

# updateProjectV2Field replaces the whole option list, so existing options
# are passed back with their original ids (to preserve them) alongside the
# two new options (left without an id so GitHub assigns one).
STATUS_FIELD_RESULT=$(gh api graphql -f query='
mutation($fieldId: ID!, $todoId: String!, $inProgressId: String!, $doneId: String!) {
  updateProjectV2Field(input: {
    fieldId: $fieldId,
    singleSelectOptions: [
      { id: $todoId, name: "Todo", color: GRAY, description: "" },
      { id: $inProgressId, name: "In Progress", color: YELLOW, description: "" },
      { name: "In Review", color: BLUE, description: "" },
      { name: "Needs human", color: RED, description: "" },
      { id: $doneId, name: "Done", color: GREEN, description: "" }
    ]
  }) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        options { id name }
      }
    }
  }
}' -f fieldId="$STATUS_FIELD_ID" -f todoId="$TODO_ID" -f inProgressId="$IN_PROGRESS_ID" -f doneId="$DONE_ID")

NEEDS_HUMAN_ID=$(jq -r '.data.updateProjectV2Field.projectV2Field.options[] | select(.name == "Needs human") | .id' <<<"$STATUS_FIELD_RESULT")

gh project link "$PROJECT_NUMBER" --owner "$OWNER" --repo "${OWNER}/${REPO_NAME}"

# --- Views -------------------------------------------------------------
# The default project ships with a single table view ("View 1"). Turn it
# into the board view, then add the three saved table views the reference
# board uses. createProjectV2View can't set a filter, so filters are applied
# in a follow-up updateProjectV2View call.
VIEWS_JSON=$(gh api graphql -f query='
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      views(first: 10) { nodes { id name } }
    }
  }
}' -f projectId="$PROJECT_ID")
DEFAULT_VIEW_ID=$(jq -r '.data.node.views.nodes[0].id' <<<"$VIEWS_JSON")

gh api graphql -f query='
mutation($viewId: ID!, $fieldIds: [ID!]) {
  updateProjectV2View(input: {
    viewId: $viewId,
    name: "Board",
    layout: BOARD_LAYOUT,
    configuration: { visibleFieldIds: $fieldIds }
  }) { projectV2View { id } }
}' -f viewId="$DEFAULT_VIEW_ID" \
   -f "fieldIds[]=$TITLE_ID" -f "fieldIds[]=$ASSIGNEES_ID" -f "fieldIds[]=$LABELS_ID" -f "fieldIds[]=$LINKED_PRS_ID" >/dev/null

create_table_view() {
  local name="$1" filter="$2"
  shift 2
  local field_ids=("$@")
  local view_id
  view_id=$(gh api graphql -f query='
mutation($projectId: ID!, $name: String!) {
  createProjectV2View(input: { projectId: $projectId, name: $name, layout: TABLE_LAYOUT }) {
    projectV2View { id }
  }
}' -f projectId="$PROJECT_ID" -f name="$name" --jq '.data.createProjectV2View.projectV2View.id')

  local -a field_args=()
  for id in "${field_ids[@]}"; do
    field_args+=(-f "fieldIds[]=$id")
  done

  gh api graphql -f query='
mutation($viewId: ID!, $filter: String!, $fieldIds: [ID!]) {
  updateProjectV2View(input: {
    viewId: $viewId,
    filter: $filter,
    configuration: { visibleFieldIds: $fieldIds }
  }) { projectV2View { id } }
}' -f viewId="$view_id" -f filter="$filter" "${field_args[@]}" >/dev/null
}

create_table_view "Up next" "status:Todo" "$TITLE_ID" "$STATUS_FIELD_ID" "$LABELS_ID"
create_table_view "My inbox" "status:\"Needs human\"" "$TITLE_ID" "$STATUS_FIELD_ID" "$LABELS_ID" "$LINKED_PRS_ID"
create_table_view "Supervised" "label:\"autonomy:supervised\"" "$TITLE_ID" "$STATUS_FIELD_ID" "$LABELS_ID" "$LINKED_PRS_ID"

echo "Project board #${PROJECT_NUMBER} ready (Todo -> In Progress -> In Review -> Needs human -> Done) with Board / Up next / My inbox / Supervised views, linked to ${OWNER}/${REPO_NAME}."
