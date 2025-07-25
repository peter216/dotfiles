#!/usr/bin/bash

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
  echo -e "${MAGENTA}Usage: $0 [-D] [-v] [-h]${RESET}"
  echo -e "${MAGENTA}  Deletes local and remote Git branches provided via stdin.${RESET}"
  echo ""
  echo -e "${MAGENTA}  Input:${RESET}"
  echo -e "${MAGENTA}    Enter a list of branches to delete, separated by spaces or commas, when prompted.${RESET}"
  echo ""
  echo -e "${MAGENTA}  Options:${RESET}"
  echo -e "${MAGENTA}    -D                : Force delete branches (git branch -D) even if unmerged.${RESET}"
  echo -e "${MAGENTA}                        Include -D in the list of branches provided via stdin.${RESET}"
  echo -e "${MAGENTA}    -v, --verbose     : Enable verbose output (set -x).${RESET}"
  echo -e "${MAGENTA}    -h, --help        : Display this help message and exit.${RESET}"
  exit 1
}

# Initialize variables #
verbose=false
force_flag=false
git_delete_flag="-d" # Default to safe delete #

# Parse command-line options #
while getopts ":hvD" opt; do
  case $opt in
  h)
    usage
    ;;
  v)
    verbose=true
    # Use magenta for informational message #
    echo -e "${MAGENTA}Verbose mode enabled.${RESET}"
    set -x
    ;;
  D)
    force_flag=true
    ;;
  \?)
    # Use red for errors #
    echo -e "${RED}Error: Invalid option: -$OPTARG${RESET}" >&2
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

# Read the input from stdin #
# Use cyan for the prompt #
read -p "$(echo -e "${CYAN}Enter the list of branches (comma or space separated, include -D for force delete): ${RESET}")" input

# Check for the force delete flag (-D) within the input string if not already set by option #
if [ "$force_flag" = false ] && [[ $input == *"-D"* ]]; then
  force_flag=true
  # Remove the -D flag from the input string to avoid treating it as a branch name #
  input=${input//-D/}
fi

# Set the appropriate git delete flag based on the force_flag #
if [ "$force_flag" = true ]; then
  # Use magenta for informational message #
  echo -e "${MAGENTA}Force flag (-D) detected. Will force delete branches.${RESET}"
  git_delete_flag="-D"
else
  git_delete_flag="-d"
fi

# Convert the input string into an array of branches, splitting by comma or space #
# Trim whitespace around branch names #
IFS=', ' read -r -a branches <<<"$(echo "$input" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

# Check if any branches were actually provided after processing #
if [ ${#branches[@]} -eq 0 ]; then #
  # Use red for errors #
  echo -e "${RED}No branch names provided. Exiting.${RESET}"
  exit 1
fi

# Loop through each branch name and attempt deletion #
for branch in "${branches[@]}"; do
  # Skip empty elements that might result from splitting #
  if [ -z "$branch" ]; then
    continue
  fi

  # Use magenta for processing information #
  echo -e "${MAGENTA}--- Processing branch: $branch ---${RESET}"

  # Attempt to delete the local branch #
  # Use cyan for script actions #
  echo -e "${CYAN}Attempting to delete local branch: git branch $git_delete_flag $branch${RESET}"
  if git branch $git_delete_flag "$branch"; then
    # Use green for success #
    echo -e "${GREEN}Successfully deleted local branch: $branch${RESET}"
  else
    # Use yellow for failure/warning #
    echo -e "${YELLOW}Failed to delete local branch: $branch. It might not exist locally, or if using '-d', it might not be fully merged.${RESET}"
  fi

  # Attempt to delete the remote branch whether or not local deletion succeeded #
  # Use cyan for script actions #
  echo -e "${CYAN}Attempting to delete remote branch: git push origin --delete $branch${RESET}"
  if git push origin --delete "$branch"; then
    # Use green for success #
    echo -e "${GREEN}Successfully deleted remote branch: $branch${RESET}"
  else
    # Use yellow for failure/warning #
    echo -e "${YELLOW}Failed to delete remote branch: $branch. It might not exist on the remote or there was another issue.${RESET}"
  fi
  # Use magenta for separator #
  echo -e "${MAGENTA}-------------------------------------${RESET}"
done

# Use magenta for final message #
echo -e "${MAGENTA}End of script${RESET}"

# Disable verbose mode if it was enabled #
if [ "$verbose" = true ]; then
  set +x
fi
