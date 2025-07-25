#!/usr/bin/bash

# Usage: ./check_old_branches.sh [-v] [-t] [-d DAYS] [-h] #
# Checks for remote branches whose last commit is older than a specified number of days. #

# Define ANSI color codes #
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
RESET='\033[0m' # No Color #

# Function to display help message #
usage() {
  # Use magenta for informational help text #
  echo -e "${MAGENTA}Usage: $0 [-v] [-t] [-d DAYS] [-h]${RESET}"
  echo -e "${MAGENTA}  Checks for remote branches whose last commit is older than a specified number of days.${RESET}"
  echo ""
  echo -e "${MAGENTA}Options:${RESET}"
  echo -e "${MAGENTA}  -h          : Print this help message and exit.${RESET}"
  echo -e "${MAGENTA}  -v          : Increase verbosity level (can be used multiple times, e.g., -vv).${RESET}"
  echo -e "${MAGENTA}  -d DAYS     : Set the number of days threshold (default: 30).${RESET}"
  echo -e "${MAGENTA}  -t          : Terse mode (outputs only a space-separated list of branch names).${RESET}"
  echo ""
  echo -e "${MAGENTA}Example:${RESET}"
  echo -e "${MAGENTA}  $0 -v -d 60   # Find branches older than 60 days with verbose output.${RESET}" #
  echo -e "${MAGENTA}  $0 -t         # Output only the names of branches older than 30 days.${RESET}" #
  exit 0
}

# Initialize variables #
verbosity=0
terse=false
days=30

# Parse command-line options #
# Handles combined flags like -vt and repeated flags like -vv #
while getopts ":hvtd:" opt; do
  case $opt in
  h)
    usage
    ;;
  v)
    # Increment verbosity for each -v found #
    verbosity=$((verbosity + 1))
    ;;
  t)
    terse=true
    ;;
  d)
    # Check if the argument for -d is a positive integer #
    if [[ "$OPTARG" =~ ^[0-9]+$ ]]; then
      days=$OPTARG
    else
      # Use red for errors #
      echo -e "${RED}Error: Invalid number of days specified for -d. Please provide a positive integer.${RESET}" >&2
      usage
    fi
    ;;
  \?)
    # Handle unknown options #
    # Use red for errors #
    echo -e "${RED}Error: Invalid option: -$OPTARG${RESET}" >&2
    usage
    ;;
  :)
    # Handle missing arguments for options that require them (like -d) #
    # Use red for errors #
    echo -e "${RED}Error: Option -$OPTARG requires an argument.${RESET}" >&2
    usage
    ;;
  esac
done
shift $((OPTIND - 1))

# Check for remaining non-option arguments (should be none) #
if [ $# -gt 0 ]; then #
  # Use red for errors #
  echo -e "${RED}Error: Unexpected arguments: $*${RESET}" >&2
  usage
fi

# Enable debug output if verbosity is high enough #
if [ $verbosity -gt 1 ]; then
  set -x
fi

# Ensure verbose and terse modes are not used together #
if [ $verbosity -gt 0 ] && [ "$terse" = true ]; then
  # Use red for errors #
  echo -e "${RED}Error: Verbose (-v) and terse (-t) modes cannot be used together.${RESET}" >&2
  usage
fi

# Fetch all remote branches #
# Suppress output in terse mode or low verbosity #
if [ "$terse" = true ] || [ $verbosity -eq 0 ]; then
  git fetch --all --prune >/dev/null 2>&1
else
  # Use cyan for script actions #
  echo -e "${CYAN}Fetching remote branches...${RESET}"
  git fetch --all --prune
fi

# Inform the user if in verbose mode #
if [ $verbosity -gt 0 ]; then
  # Use magenta for informational messages #
  echo -e "${MAGENTA}Verbose mode enabled (level $verbosity).${RESET}"
  echo -e "${MAGENTA}Searching for remote branches with last commit date more than $days days ago...${RESET}"
fi

# Get all remote branch names, excluding the HEAD pointer #
# Ensure correct parsing even with unusual branch names #
mapfile -t branches < <(git branch -r --format='%(refname:short)' | sed 's/^origin\///' | grep -v '^HEAD$')

# Get the current date timestamp #
current_date=$(date +%s)

# Initialize an array to hold branches identified as old #
old_branches=()

# Loop through each branch and check the last commit date #
for branch in "${branches[@]}"; do
  # Skip empty branch names if any occurred #
  if [ -z "$branch" ]; then
    continue
  fi

  # Get the last commit date timestamp for the remote branch #
  # Use --date=unix for direct timestamp comparison #
  last_commit_timestamp=$(git log -1 --format=%cd --date=unix "origin/$branch" --)

  # Handle cases where git log might fail (e.g., branch deleted after fetch but before log) #
  if [ -z "$last_commit_timestamp" ]; then
    if [ $verbosity -gt 0 ]; then
      # Use yellow for warnings #
      echo -e "${YELLOW}Warning: Could not get commit date for branch: $branch. Skipping.${RESET}" >&2
    fi
    continue
  fi

  # Calculate the difference in days #
  diff_seconds=$((current_date - last_commit_timestamp))
  # Use integer division #
  diff_days=$((diff_seconds / 86400))

  # Print details in verbose mode #
  if [ $verbosity -gt 0 ]; then
    last_commit_date_iso=$(date -d "@$last_commit_timestamp" --iso-8601=seconds)
    # Use magenta for informational details #
    echo -e "${MAGENTA}Branch: $branch, Last Commit Date: $last_commit_date_iso, Days Ago: $diff_days${RESET}"
  fi

  # Check if the last commit date is older than the threshold #
  if [ $diff_days -gt $days ]; then
    old_branches+=("$branch")
  fi
done

# Output the results based on the mode (terse or normal/verbose) #
if [ ${#old_branches[@]} -eq 0 ]; then #
  # Only print if not in terse mode #
  if [ "$terse" = false ]; then
    # Use green for success/no-action-needed message #
    echo -e "${GREEN}No remote branches found with the last commit older than $days days.${RESET}"
  fi
else
  # Normal/Verbose output #
  if [ "$terse" = false ]; then
    # Use yellow for the list header as it indicates potential action needed #
    echo -e "${YELLOW}Remote branches with last commit older than $days days:${RESET}"
    # Print each branch name (no specific color, or maybe yellow?) #
    printf '%s\n' "${old_branches[@]}"
  # Terse output #
  else
    # Print branches space-separated on a single line, no color for terse mode #
    echo -n "${old_branches[*]} "
  fi
fi

# Add a final newline in terse mode if branches were found #
if [ "$terse" = true ] && [ ${#old_branches[@]} -gt 0 ]; then #
  echo
fi

# Disable debug output if it was enabled #
if [ $verbosity -gt 1 ]; then
  set +x
fi
