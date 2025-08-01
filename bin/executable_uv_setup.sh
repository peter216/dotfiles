#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# uv_setup.sh
#
# Author: Peter Rubenstein (prube194@marriott.com)
# Purpose: Initialize a new uv project with a virtual environment.
# License: MIT License
#
# Description:
#   This script initializes a new uv project with a virtual environment.
#   It checks for existing virtual environments and projects, and handles them accordingly.
#   It also handles an existing pyproject.toml file, extracting metadata and dependencies.
#   The script requires the uv tool to be installed and available in the PATH.
#   It will create a new project directory named uv_<current_directory_name> and set up
#   a virtual environment within it. It will also create a symlink to the project directory
#   named .uv. The script will add ipython as a dev dependency and sync any existing
#   requirements from requirements.txt.
#
# Usage:
#   uv_setup.sh
#   DEBUG=true uv_setup.sh
#   UV_PYTHON=python3.10 uv_setup.sh
#
# Dependencies:
#   - uv tool (https://docs.astral.sh/uv/)
#
# Version: 0.1.0
# Date: 2025-06-11
#
# Notes:
#   - You should be in the root directory of your project when running this script.
#   - The script respects the DEBUG environment variable to control debug output.
#   - The UV_PYTHON environment variable can be set to specify the Python version for the virtual environment.
# -----------------------------------------------------------------------------
#
# TODO: Not working with authors field in pyproject.toml

set -e # Exit on error

## --- ANSI Color Codes ---
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m' # No Color

DEBUG=false
UV_PROJECT_NAME=""

log_debug() {
    if [ "$DEBUG" = true ]; then
        echo -e "${MAGENTA}[DEBUG] $1${RESET}"
    fi
}

log_info() {
    echo -e "${MAGENTA}[INFO] $1${RESET}"
}

log_action() {
    echo -e "${CYAN}[ACTION] $1${RESET}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${RESET}"
}

log_warn() {
    echo -e "${YELLOW}[CHANGE] $1${RESET}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${RESET}"
}

# Are we on Windows?
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    WIN=1
    log_debug "Windows environment detected"
else
    WIN=0
    log_debug "Windows environment not detected. Assume Linux"
fi

# Get cli arguments
while getopts ":vp:" opt; do
    case ${opt} in
    v)
        DEBUG=true
        set -x # Enable debug mode
        ;;
    p)
        UV_PROJECT_NAME=$OPTARG
        log_info "Using UV_PROJECT_NAME: $UV_PROJECT_NAME"
        ;;
    \?)
        echo "Usage: $0 [-v]"
        exit 1
        ;;
    esac
done

if [ -n "$UV_PROJECT_NAME" ]; then
    log_info "Using UV_PROJECT_NAME input variable: $UV_PROJECT_NAME"
    PROJ=$UV_PROJECT_NAME
else
    log_info "No UV_PROJECT_NAME input variable set. Using current directory name."
    BNAME=$(basename "$PWD")
    PROJ=uv_$BNAME
fi
EXISTING_TOML=false

log_debug "Current directory: $PWD"
log_debug "Project name: $PROJ"

# Check for uv in PATH
if ! command -v uv &>/dev/null; then
    log_error "uv command not found. Please install uv tool first."
    exit 1
fi

# For idempotency, check if the project directory already exists
if [ -d $PROJ ]; then
    log_warn "$PROJ directory exists. Delete it? (y/n)"
    read -r answer
    if [ "$answer" != "y" ]; then
        log_info "Exiting without changes."
        exit 0
    fi
    log_action "Deleting existing project setup $PROJ"
    rm -rf $PROJ
    log_success "Deleted existing project setup."
fi

if [ -f ./pyproject.toml ]; then
    log_info "pyproject.toml found. Using it to initialize the project."
    # Moving the file is required because uv will refuse to initialize a project
    # if it finds an existing pyproject.toml
    # Plus we now have a backup of the original file
    mv pyproject.toml pyproject.toml.bak
    EXISTING_TOML=true
    log_debug "Moved pyproject.toml to pyproject.toml.bak"
fi

log_action "Initializing uv project: $PROJ"
uv init --no-workspace $PROJ
log_success "uv project initialized."

# Again, for idempotency, check if the symlink .uv already exists and recreate it
if [ -d .uv ]; then
    log_warn "Removing and recreating symlink to .uv"
    if [[ $WIN -eq 1 ]]; then
        rm -vrf .uv
    else
        rm -vf .uv
    fi
fi

# In Windows, .uv is just a text file with the name of the project dir
if [[ WIN -eq 1 ]]; then
    log_action "Creating a pointer to $PROJ named .uv"
    echo $PROJ >.uv
else
    log_action "Creating symlink .uv -> $PROJ"
    ln -s $PROJ .uv
    log_success "Symlink created."
fi

log_action "Creating virtual environment for $PROJ"
uv venv --project $PROJ
log_success "Virtual environment created."

log_action "Activating virtual environment for $PROJ"
# if Windows, use Scripts instead of bin
if [[ WIN -eq 1 ]]; then
    source $PROJ/.venv/Scripts/activate
else
    source $PROJ/.venv/bin/activate
fi
log_success "Virtual environment activated."

if [ $EXISTING_TOML = true ]; then
    log_info "Using existing pyproject.toml to seed project metadata."
    # The procedure here is to extract the name, version, and requires-python from the NEW pyproject.toml
    # but keep everything else from the original, including dependencies.
    name=$(grep "name =" $PROJ/pyproject.toml | cut -d" " -f3 | tr -d '"')
    version=$(grep "version =" $PROJ/pyproject.toml | cut -d" " -f3 | tr -d '"')
    pyversion=$(grep "requires-python =" $PROJ/pyproject.toml | cut -d" " -f3 | tr -d '"')
    log_debug "Extracted name: $name, version: $version, requires-python: $pyversion"
    log_action "Recreating pyproject.toml with the existing dependencies and the name and version requested."
    cp pyproject.toml.bak pyproject.toml.temp
    sed -i "s/name = .*//" pyproject.toml.temp
    sed -i "s/version = .*//" pyproject.toml.temp
    sed -i "s/requires-python = .*//" pyproject.toml.temp
    # Insert the new values after the line matching regex "^\[project\]$"
    NEWBLOCK="name = \"$name\"\nversion = \"$version\"\nrequires-python = \"$pyversion\""
    sed -i "/^\[project\]/a $NEWBLOCK" pyproject.toml.temp
    mv pyproject.toml.temp $PROJ/pyproject.toml
    log_debug "Updated $PROJ/pyproject.toml with dependencies from original pyproject.toml"
    log_action "Syncing dependencies with uv"
    if uv sync --project $PROJ --active || true; then
        log_success "Project metadata and dependencies synced."
    else
        log_error "Failed to sync project metadata and dependencies."
        exit 1
    fi
fi

# Loop through requirements files and add them if present
for REQ_FILE in requirements.txt requirements.in; do
    # Check if the requirements file exists
    if [ -f $REQ_FILE ]; then
        log_action "Adding requirements from $REQ_FILE"
        # Try to add requirements, handle failure gracefully
        if uv add -r $REQ_FILE --project $PROJ --active; then
            log_success "Requirements from $REQ_FILE added."
        else
            log_warn "Failed to add requirements from $REQ_FILE. Continuing..."
            log_action "Attempting alternate method to add requirements (uv pip install)"
            log_action "Performing dry run for pip install from $REQ_FILE"
            if PIP_DEPS=$(uv pip install -r $REQ_FILE --project $PROJ --dry-run 2>&1); then
                log_debug "Dry run successful for pip install from $REQ_FILE."
            else
                log_error "Dry run failed for pip install from $REQ_FILE."
                exit 1
            fi
            if uv pip install -r $REQ_FILE --project $PROJ; then
                log_success "Requirements from $REQ_FILE added via pip."
            else
                log_error "Failed to add requirements from $REQ_FILE via pip."
                exit 1
            fi
            # Append the pip dependencies in a comment block to the pyproject.toml file
            echo "# PIP dependencies added from $REQ_FILE" >>$PROJ/pyproject.toml
            log_debug "Appending pip dependencies to $PROJ/pyproject.toml"
            echo "$PIP_DEPS" | grep '+' | sed 's/+/-/' | sed 's/^/# /' >>$PROJ/pyproject.toml
        fi
    else
        log_debug "$REQ_FILE not found, skipping."
    fi
done

log_action "Adding ipython as a dev dependency." # A personal preference for interactive development.
uv add ipython --dev --project $PROJ --active
log_success "ipython added as a dev dependency."

log_success "Project $PROJ initialized with virtual environment and dependencies."
