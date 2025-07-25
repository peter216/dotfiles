#!/usr/bin/env bash

set -e
set -o pipefail

DEBUG=0
## --- ANSI Color Codes ---
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m' # No Color

if [ -t 1 ]; then
    COLOR=1
else
    COLOR=0
fi

if [[ $1 == "--help" ]] || [[ $1 == "-h" ]]; then
    echo
    echo "auto_git_backup.sh"
    echo
    echo "Usage: $0 [--verbose|-v]"
    echo "  --verbose, -v: Enable verbose output"
    echo "  --help, -h: Show this help message"
    echo
    echo "This script will search for git repositories under \$HOME/git and create autobackup"
    echo "branches if a .backup file is found in the repository root."
    echo
    echo "Features:"
    echo "- Searches for git repositories under \$HOME/git, excluding .venv and .collections"
    echo "- Prunes old autobackup branches to keep only the 3 most recent ones."
    echo "- Checks for staged or unstaged changes and creates a backup branch"
    echo "- if changes are detected or if the current branch is ahead of its remote."
    echo
    echo "- If no .backup file is found, it will skip the autobackup for that repository."
    echo "- If the script is run with --verbose or -v, it will print debug messages."
    echo
    exit 0
fi

if [[ $1 == "--verbose" ]] || [[ $1 == "-v" ]]; then
    DEBUG=1
    shift # Remove the verbose flag from the arguments
fi

# Logging functions
log_debug() {
    # Debug messages in magenta
    if [[ $DEBUG -eq 0 ]]; then
        return 0 # Skip debug messages if DEBUG is not set
    elif [[ $COLOR -eq 0 ]]; then
        echo "[DEBUG] $*"
    else
        echo -e "${MAGENTA}[DEBUG]${RESET} $*"
    fi
}
log_info() {
    # Info messages in cyan
    if [[ $COLOR -eq 0 ]]; then
        echo "[INFO] $*"
    else
        echo -e "${CYAN}[INFO]${RESET} $*"
    fi
}
log_warn() {
    # Warning messages in yellow
    if [[ $COLOR -eq 0 ]]; then
        echo "[WARNING] $*"
    else
        echo -e "${YELLOW}[WARNING]${RESET} $*"
    fi
}
log_error() {
    # Error messages in red
    if [[ $COLOR -eq 0 ]]; then
        echo "[ERROR] $*"
    else
        echo -e "${RED}[ERROR]${RESET} $*"
    fi
}
log_success() {
    # Success messages in green
    if [[ $COLOR -eq 0 ]]; then
        echo "[SUCCESS] $*"
    else
        echo -e "${GREEN}[SUCCESS]${RESET} $*"
    fi
}

autobackup_same_as_head() {
    # If the most recent autobackup branch has the no diff to HEAD, skip autobackup
    latest_autobackup_branch=$(git for-each-ref --sort=-committerdate --format='%(refname:short)' refs/heads/autobackup-* | head -n 1)
    if [[ -n "$latest_autobackup_branch" ]]; then
        diff_to_head=$(git diff "$latest_autobackup_branch" HEAD)
        if [[ -z "$diff_to_head" ]]; then
            log_debug "Latest autobackup branch '$latest_autobackup_branch' is the same as HEAD, skipping autobackup."
            return 0
        else
            log_debug "Latest autobackup branch '$latest_autobackup_branch' has changes compared to HEAD, proceeding with autobackup."
            return 1
        fi
    else
        log_debug "No autobackup branches found, proceeding with autobackup."
        return 1
    fi
}

if [ -t 1 ]; then
    exec >>/home/prube194/logs/auto_git_backup_debug.log 2>&1
    echo "Script started at $(date)"
    log_debug "Current PATH: $PATH"
fi

# Find all git repositories in the hierarchy
if [[ -z "$HOME" ]]; then
    log_error "HOME environment variable is not set."
    exit 1
fi
log_debug "Searching for git repositories under $HOME/git ..."
gitdirs=$(find $HOME/git -type d \( -name ".venv" -o -name ".collections" $EXTRA_DIRS_STRING \) -prune -o -type d -name ".git" 2>/dev/null)
gitdirs=$(echo "$gitdirs" "$HOME/bin/.git")

# Check if smart_push is in path
smart_push_path=$(which smart_push)
if [ -z "$smart_push_path" ]; then
    # Try the Windows way
    mybindir=$(echo $PATH | tr ':' '\n' | grep -E "prube194\\bin$" | head -n 1)
    smart_push_path="$mybindir/smart_push"
fi

if [ ! -x "$smart_push_path" ]; then
    push_command="git push"
    log_debug "smart_push not found in PATH, using git push instead"
else
    push_command="$smart_push_path"
    log_debug "smart_push found at $smart_push_path"
fi
log_info "Using push command: $push_command"

for gitdir in $gitdirs; do
    log_info "Found git repository: $gitdir"
    # Get the repo root
    repo_root="$(dirname "$gitdir")"
    cd "$repo_root" || {
        log_error "Failed to cd to $repo_root"
        continue
    }

    # Check for .backup file in the repo root
    if [[ -f ".backup" ]]; then
        log_info ".backup file found in $repo_root, proceeding with autobackup."

        # Prune autobackup branches if more than 3 exist
        autobackup_branches=($(git for-each-ref --format='%(refname:short) %(committerdate:iso8601)' refs/heads/autobackup-* | sort -k2 | awk '{print $1}'))
        num_autobackup=${#autobackup_branches[@]}
        if ((num_autobackup > 3)); then
            num_to_delete=$((num_autobackup - 3))
            log_warn "Found $num_autobackup autobackup branches, deleting $num_to_delete oldest to keep only 3."
            for ((i = 0; i < num_to_delete; i++)); do
                old_branch="${autobackup_branches[$i]}"
                # Delete local branch
                git branch -D "$old_branch" && log_info "Deleted local branch $old_branch"
                # Delete remote branch
                $push_command origin --delete "$old_branch" && log_info "Deleted remote branch $old_branch"
            done
        fi

        # Check for staged or unstaged changes
        has_changes=false
        if [[ -n "$(git status --porcelain)" ]]; then
            has_changes=true
        fi

        current_branch="$(git rev-parse --abbrev-ref HEAD)"
        log_debug "Current branch: $current_branch"

        # Check if branch is tracking a remote
        if git rev-parse --abbrev-ref --symbolic-full-name @{u} &>/dev/null; then
            upstream="$(git rev-parse --abbrev-ref --symbolic-full-name @{u})"
            ahead_count=$(git rev-list --left-right --count "$current_branch...$upstream" | awk '{print $1}')
            if ((ahead_count > 0)); then
                log_info "Current branch is ahead of its remote ($ahead_count commits). Checking for previous autobackups."
                if autobackup_same_as_head; then
                    log_warn "Branch had changes. Creating autobackup branch."
                    has_changes=1
                else
                    log_info "Skipping autobackup: HEAD is identical to latest autobackup branch."
                    continue
                fi
            fi
        else # If the current branch is not tracking a remote, automatically set is_ahead to true
            log_info "Current branch '$current_branch' is not tracking a remote. Checking for previous autobackups."
            if autobackup_same_as_head; then
                log_info "Skipping autobackup: HEAD is identical to latest autobackup branch"
            else
                log_warn "Branch has changes, creating autobackup branch."
            fi
        fi

        # Only create autobackup branch if changes or branch is ahead
        if [[ "$has_changes" -eq 0 || "$is_ahead" -eq 0 ]]; then
            # Create a new branch with timestamp
            log_warn "Changes detected in $repo_root, creating a backup branch."
            timestamp="$(date +autobackup-%y%m%d_%H%M%S)"
            log_debug "Creating new branch: $timestamp"
            git checkout -b "$timestamp"

            # Stage and commit all changes if there are any
            if [[ "$has_changes" -eq 0 ]]; then
                log_debug "Staging and committing all changes."
                git add -A
                git commit -m "Autobackup commit on $timestamp" --no-verify
            fi

            # Push the new branch to origin and set upstream
            log_debug "Pushing branch $timestamp to origin."
            $push_command -u origin "$timestamp"
            # Check if branch has pushed successfully
            branch_check=$(git ls-remote --heads origin "$timestamp")
            if [[ -z "$branch_check" ]]; then
                log_error "Failed to push branch $timestamp to origin."
            else
                log_success "Branch $timestamp pushed successfully to origin."
            fi
            # Return to the original branch
            log_debug "Returning to original branch: $current_branch"
            git checkout "$current_branch"
            # Restore working directory to original state if there were changes
            git checkout $timestamp -- .
            log_debug "Restored working directory to original state."
        else
            log_debug "No changes or unpushed commits detected in $repo_root, skipping autobackup."
        fi
    else
        log_debug ".backup file not found in $repo_root, skipping autobackup."
    fi
done
