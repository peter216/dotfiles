#!/usr/bin/bash

## This script does the following:
##   - Stashes current changes temporarily.
##   - Determines the set of files to lint (staged, or based on --from/--to).
##   - Optionally filters out files matching an ignore pattern.
##   - Runs pre-commit hooks (yamllint, actionlint, ruff, ruff-format) on the target files.
##   - Runs ansible-lint --fix on the target YAML files.
##   - Stashes the state after linting.
##   - Creates a diff log showing changes made by the linters.
##   - Cleans up temporary branches.

set -e ## Exit immediately if a command exits with a non-zero status.

## --- ANSI Color Codes ---
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m' # No Color

ANSIBLELINT=/home/prube194/git/global_venv/.venv/GLOBAL/bin/ansible-lint
PRECOMMIT=/home/prube194/git/global_venv/.venv/GLOBAL/bin/pre-commit

## Usage function
usage() {
    echo -e "${RED}Usage: prelint.sh [--from <ref>] [--to <ref>] [--ignore <regex>] [-v] [-h]${RESET}"
    echo -e "  ${MAGENTA}--from <ref>${RESET}: Specify the starting point for diff (e.g., a branch, tag, commit hash)."
    echo -e "  ${MAGENTA}--to <ref>${RESET}:   Specify the ending point for diff (defaults to HEAD if --from is specified)."
    echo -e "  ${MAGENTA}--ignore <regex>${RESET}: ERE regex pattern to exclude files from linting."
    echo -e "  ${MAGENTA}-v${RESET}:           Enable verbose output."
    echo -e "  ${MAGENTA}-h${RESET}:           Show this help message."
    exit 1
}

## --- Argument Parsing ---
VERBOSE=false
FROM_REF=""
TO_REF=""
ignore_regex=""
use_diff_range=false
VSWITCH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
    -h)
        usage
        ;;
    --from)
        if [[ -z "$2" ]]; then
            echo -e "${RED}Error: --from requires a reference.${RESET}" >&2
            usage
        fi
        FROM_REF="$2"
        use_diff_range=true
        shift 2
        ;;
    --to)
        if [[ -z "$2" ]]; then
            echo -e "${RED}Error: --to requires a reference.${RESET}" >&2
            usage
        fi
        TO_REF="$2"
        use_diff_range=true # Also set if only --to is given, handled later
        shift 2
        ;;
    --staged)
        add_staged=true
        shift
        ;;
    --ignore)
        if [[ -z "$2" ]]; then
            echo -e "${RED}Error: --ignore requires a regex pattern.${RESET}" >&2
            usage
        fi
        ignore_regex="$2"
        shift 2
        ;;
    -v)
        VERBOSE=true
        VSWITCH="--verbose"
        shift
        ;;
    *)
        echo -e "${RED}Error: Unknown option '$1'${RESET}" >&2
        usage
        ;;
    esac
done

if [ "$VERBOSE" = true ]; then
    set -x ## Enable debug output for linter commands
fi

## Validate --from/--to combination
if $use_diff_range && [[ -z "$FROM_REF" ]] && [[ -n "$TO_REF" ]]; then
    echo -e "${RED}Error: Using --to without --from is not supported.${RESET}" >&2
    usage
fi
## Default --to to HEAD if only --from is specified
if $use_diff_range && [[ -n "$FROM_REF" ]] && [[ -z "$TO_REF" ]]; then
    TO_REF="HEAD"
fi

## --- Script Setup ---
random_number=$((10000000 + RANDOM % 90000000))
start_branch=$(git rev-parse --abbrev-ref HEAD)
pre_fix_branch="pre-commit-stash-$random_number"
post_fix_branch="post-fix-stash-$random_number"
LOG_DIR="logs"
PRE_COMMIT_LOG="$LOG_DIR/pre-commit.log"
ANSIBLE_LINT_LOG="$LOG_DIR/ansible-lint.log"
DIFF_LOG="$LOG_DIR/pre-commit-diff.log"

## Create logs directory
mkdir -p "$LOG_DIR"
## Clear previous logs for this run
>"$PRE_COMMIT_LOG"
>"$ANSIBLE_LINT_LOG"
>"$DIFF_LOG"

echo -e "${MAGENTA}Starting prelint script...${RESET}"
echo -e "${MAGENTA}Current branch: $start_branch${RESET}"
echo -e "${MAGENTA}Temporary pre-fix branch: $pre_fix_branch${RESET}"
echo -e "${MAGENTA}Temporary post-fix branch: $post_fix_branch${RESET}"

## --- Stash Initial State ---
## Create a temporary branch to hold the state *before* linting
echo -e "${CYAN}Stashing initial state...${RESET}"
git checkout -b "$pre_fix_branch"
## Add all current changes (staged and unstaged)
git add --all .
## Commit these changes temporarily
## Use --no-verify to prevent the pre-commit hook from running here
if git diff --cached --quiet && git diff --quiet; then
    echo -e "${YELLOW}No changes detected to stash before linting.${RESET}"
    ## If there are no changes, we might still want to run based on --from/--to
    ## Create an empty commit to have a starting point if needed, or just proceed
    git commit --allow-empty --no-verify -m "Prelint: No changes detected before linting"
else
    git commit --no-verify -m "Prelint: Stashing changes before linting"
fi

## --- Determine Files to Lint ---
ALL_FILES_TO_LINT=""
YAML_FILES_TO_LINT=""

if $use_diff_range; then
    echo -e "${CYAN}Determining files changed between $FROM_REF and $TO_REF...${RESET}"
    ## Get files changed in the specified range
    ALL_FILES_TO_LINT=$(git diff --name-only "$FROM_REF" "$TO_REF")
fi
if $add_staged; then
    echo -e "${CYAN}Adding staged files to the list...${RESET}"
    ## Get currently staged files
    ALL_FILES_TO_LINT=$(echo "$ALL_FILES_TO_LINT" && git diff --cached --name-only)
fi

## Filter YAML files
YAML_FILES_TO_LINT=$(echo "$ALL_FILES_TO_LINT" | grep '\.yml$' || true) ## Use || true to avoid error if grep finds nothing

## Apply ignore regex if provided
if [[ -n "$ignore_regex" ]]; then
    echo -e "${CYAN}Ignoring files matching regex: $ignore_regex${RESET}"
    ALL_FILES_TO_LINT=$(echo "$ALL_FILES_TO_LINT" | grep -vE "$ignore_regex" || true)
    YAML_FILES_TO_LINT=$(echo "$YAML_FILES_TO_LINT" | grep -vE "$ignore_regex" || true)
fi

## Check if there are files to lint
if [[ -z "$ALL_FILES_TO_LINT" ]]; then
    echo -e "${YELLOW}No files found to lint after filtering. Exiting.${RESET}"
    ## Clean up the temporary branch
    git checkout "$start_branch"
    git branch -D "$pre_fix_branch"
    exit 0
fi

echo -e "${MAGENTA}Files to be processed by pre-commit hooks:${RESET}"
echo "$ALL_FILES_TO_LINT" | sed 's/^/  /' || echo -e "  ${YELLOW}(None)${RESET}"
echo -e "${MAGENTA}YAML files to be processed by ansible-lint:${RESET}"
echo "$YAML_FILES_TO_LINT" | sed 's/^/  /' || echo -e "  ${YELLOW}(None)${RESET}"

## --- Run Linters ---
echo -e "${CYAN}Running pre-commit hooks...${RESET}"

## Run pre-commit hooks, tee output to main log
## Pass files as arguments; use xargs if the list is very long
echo "$ALL_FILES_TO_LINT" | xargs --no-run-if-empty $PRECOMMIT run yamllint --hook-stage manual $VSWITCH --files 2>&1 | tee -a "$PRE_COMMIT_LOG"
echo "$ALL_FILES_TO_LINT" | xargs --no-run-if-empty $PRECOMMIT run actionlint --hook-stage manual $VSWITCH --files 2>&1 | tee -a "$PRE_COMMIT_LOG"
echo "$ALL_FILES_TO_LINT" | xargs --no-run-if-empty $PRECOMMIT run ruff --hook-stage manual $VSWITCH --files 2>&1 | tee -a "$PRE_COMMIT_LOG"
echo "$ALL_FILES_TO_LINT" | xargs --no-run-if-empty $PRECOMMIT run ruff-format --hook-stage manual $VSWITCH --files 2>&1 | tee -a "$PRE_COMMIT_LOG"

## Run ansible-lint separately for YAML files
if [[ -n "$YAML_FILES_TO_LINT" ]]; then
    echo -e "${CYAN}Running ansible-lint...${RESET}"
    ## Run ansible-lint with --fix, tee output to both its own log and the main log
    echo "$YAML_FILES_TO_LINT" | xargs --no-run-if-empty $ANSIBLELINT --fix 2>&1 | tee "$ANSIBLE_LINT_LOG" >>"$PRE_COMMIT_LOG"
else
    echo -e "${YELLOW}Skipping ansible-lint as no relevant YAML files were found.${RESET}"
fi

if [ "$VERBOSE" = true ]; then
    set +x ## Disable debug output
fi

## --- Stash Post-Fix State ---
echo -e "${CYAN}Stashing state after linting fixes...${RESET}"
## Create a new branch to hold the state *after* linting
git checkout -b "$post_fix_branch"
## Add all changes made by the linters
git add --all .
## Commit the post-linting state
if git diff --cached --quiet; then
    echo -e "${YELLOW}Linters made no changes.${RESET}"
    git commit --allow-empty --no-verify -m "Prelint: No changes made by linters"
else
    echo -e "${YELLOW}Linters made changes.${RESET}" ## Indicate that changes were made
    git commit --no-verify -m "Prelint: Stashing changes after linter fixes"
fi

## --- Compare Changes and Report ---
echo -e "${CYAN}Comparing pre-fix and post-fix states...${RESET}"
## Compare the two temporary branches to see what the linters changed
git diff "$pre_fix_branch" "$post_fix_branch" >"$DIFF_LOG" || true ## Allow diff to return non-zero if there are changes

echo -e "${GREEN}Linting process complete.${RESET}"
echo -e "${MAGENTA}Combined linter output log: $PRE_COMMIT_LOG${RESET}"
echo -e "${MAGENTA}Ansible-lint specific output log: $ANSIBLE_LINT_LOG${RESET}"
echo -e "${MAGENTA}Diff of changes made by linters: $DIFF_LOG${RESET}"

echo -e "${GREEN}Script finished.${RESET} ${YELLOW}Please review the logs and the changes applied to your working directory.${RESET}"
