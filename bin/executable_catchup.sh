#!/usr/bin/bash

# This script will pull the latest changes from all branches in the repository.
# If the branch is behind, it will pull the latest changes.
# If the branch is ahead, it will print a warning message.
# If the branch is up to date, it will print a message saying so.
#
# Author:
#   - Peter Rubenstein (prube194@marriott.com)

# Get cli arguments
# while getopts ":v" opt; do
# Set getopts to accept -v as the flag for verbose
while getopts ":v" opt; do
  case ${opt} in
  v)
    VERBOSE=true
    set -x
    ;;
  \?)
    echo "Usage: catchup.sh [-v]"
    exit 1
    ;;
  esac
done

# Get the name of the current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Fetch all branches
git fetch --all

# Get all branch names
branches=$(git branch -r | grep -v '\->' | sed 's/origin\///')

# Check if smart_pull is in path
if ! command -v smart_pull &>/dev/null; then
  pull_command="git pull"
  echo "⚠️ smart_pull not found in PATH, using git pull instead."
else
  pull_command="smart_pull"
  echo "Using smart_pull for pulling changes."
fi

# Loop through each branch
for branch in $branches; do

  # Check if the branch is up to date
  output=$(git rev-list --left-right --count origin/$branch...$branch -- 2>&1)
  if [[ $output == "fatal: bad revision"* ]]; then
    echo "⚠️ Warning: $output". Attempting to fix...
    git checkout $branch --
    output=$(git rev-list --left-right --count origin/$branch...$branch -- 2>&1)
    if [[ $output == "fatal"* ]]; then
      echo "❌ Error: $output"
      echo "Skipping branch $branch."
      continue
    # Looking for output like "0    0" which means the branch is up to date
    elif [[ $(tr -d [:space:] <<<"$output") == "00" ]]; then
      echo "✅ Successfully set up tracking for branch $branch."
    else
      echo "❌ Error: $output"
      echo "Skipping branch $branch."
      continue
    fi
  fi
  read behind ahead <<<"$output"
  if [[ $behind -eq 0 ]]; then
    if [[ $VERBOSE ]]; then
      echo "✔️ Branch $branch is up to date."
    fi
  else
    echo "Branch $branch is behind by $behind commits. Pulling latest changes..."
    echo "Checking out branch: $branch"
    # Checkout the branch
    git checkout $branch --
    pull_result=$($pull_command)
    printf '%s\n' "$pull_result"
    pull_result_line_1=$(echo $pull_result | head -n 1)
    if [[ $pull_result_line_1 == "There is no tracking information for the current branch"* ]]; then
      echo "⚠️ WARNING: No tracking information for the current branch. Setting up tracking information..."
      git branch --set-upstream-to=origin/$branch $branch --
      echo "Tracking information set up for branch $branch."
      if $pull_command; then
        echo "✅ Successfully pulled latest changes for branch $branch."
      else
        echo "❌ Failed to pull latest changes for branch $branch."
      fi
    fi
  fi
  if [[ $ahead -ne 0 ]]; then
    echo "⚠️ WARNING: Branch $branch is ahead by $ahead commits."
  fi
done

# Checkout back to the current branch
git checkout $current_branch
