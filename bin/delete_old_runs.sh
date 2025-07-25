#!/bin/bash

# Define color variables
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
# REPO="your-username/your-repo"
# WORKFLOW_NAME="your-workflow.yml"

if [[ -n $1 && $1 == "TEST" ]]; then
  echo -e "${GREEN}TEST MODE ENABLED${NC}"
  TEST_MODE=true
else
  TEST_MODE=false
fi

# Get the list of workflow runs, sorted by creation date, and skip the first 10
RUN_IDS=$(gh run list --limit 1000 --json databaseId --jq '.[].databaseId' | /usr/bin/sort -rn)
LAST_10=$(echo "$RUN_IDS" | tr " " "\n" | head -n 10 | tr '\n' ', ')

echo -e "${BLUE}Not touching the last 10 workflow runs${NC}"
echo -e "${BLUE}$LAST_10${NC}"
echo

# Loop through the run IDs and delete each one
if [ "$TEST_MODE" = true ]; then
  echo -e "${BLUE}TEST MODE ENABLED, NOT DELETING ANY RUNS${NC}"
else
  for RUN_ID in $(echo "$RUN_IDS" | tail -n +11); do
    echo -e "${YELLOW}Deleting run $RUN_ID${NC}"
    gh run delete $RUN_ID
  done
  echo -e "${GREEN}Deleted all but the last 10 workflow runs${NC}"
fi
