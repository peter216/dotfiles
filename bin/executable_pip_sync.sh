#!/bin/bash
# pip_sync.sh
# This script is used to sync a Python virtual environment with a requirements file.
# It also installs the "global_venv" site-packages directory to the virtual environment as a .pth file.
# The intention is to avoid duplicate installations of packages that are already installed in the global virtual environment, while allowing additional packages to be installed in the local virtual environment.
# It creates a new virtual environment if it does not exist, compiles the requirements.in file,
# and installs the dependencies listed in requirements.txt. It also handles logging and error checking.
# Usage: ./pip_sync.sh <syncdir> <venv-name>

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <syncdir> <venv-name>"
    exit 1
fi

VERBOSE=false

# Take in cli options
while getopts ":d:n:v" opt; do
    case $opt in
    d) SYNCDIR="$OPTARG" ;;
    n) VENV_NAME="$OPTARG" ;;
    v)
        VERBOSE=true
        echo "Verbose mode enabled."
        ;;
    \?) echo "Invalid option: -$OPTARG" >&2 ;;
    :) echo "Option -$OPTARG requires an argument." >&2 ;;
    esac
done

# Alternatively, accept positional arguments
SYNCDIR=${1:-$SYNCDIR}
VENV_NAME=${2:-$VENV_NAME}
# Check if SYNCDIR and VENV_NAME are set
if [ -z "$SYNCDIR" ] || [ -z "$VENV_NAME" ]; then
    echo "Both syncdir and venv-name must be provided."
    exit 1
fi

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Function to check a specific exit code passed as an argument #
check_specific_exit_code() {
    local exit_code=$1
    local command_name=$2 # Optional name of the command for better error messages #
    if [ $exit_code -ne 0 ]; then
        echo
        if [ -n "$command_name" ]; then
            echo -e "${RED}$command_name failed with Exit Code: $exit_code. Aborting.${NC}"
        else
            echo -e "${RED}An error occurred (Exit Code: $exit_code). Aborting.${NC}"
        fi
        echo -e "${RED}Exiting.${NC}"
        exit $exit_code
    fi
}

if $VERBOSE; then
    set -x # Enable verbose mode
fi

# Get the python version of the global virtual environment
PYTHON_VERSION=$(ls ~/git/global_venv/.venv/GLOBAL/lib | grep -Eo 'python[0-9]+\.[0-9]+' | head -n 1)
check_specific_exit_code $? "Get Python version"
# Check if the python version is empty
if [ -z "$PYTHON_VERSION" ]; then
    echo -e "${RED}Python version not found. Please check your global virtual environment.${NC}"
    exit 1
fi
echo -e "${CYAN}Python version: $PYTHON_VERSION${NC}"

# Check if the sync directory exists
if [ ! -d "$SYNCDIR" ]; then
    echo -e "${RED}Sync directory $SYNCDIR does not exist. Please check the path.${NC}"
    exit 1
fi

# Check if the logs directory exists, if not create it
# Changed log directory path to be relative to SYNCDIR #
LOG_DIR="$SYNCDIR/logs"
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}Logs directory $LOG_DIR does not exist. Creating it...${NC}"
    # Create the logs directory
    mkdir "$LOG_DIR"
    check_specific_exit_code $? "Create logs directory"
fi
# Define log file path #
REQUIREMENTS_LOG="$LOG_DIR/requirements.log"

cd "$SYNCDIR"
check_specific_exit_code $? "Change directory to $SYNCDIR" # Check if cd was successful #

# Check if the venv directory exists
if [ ! -d ".venv/$VENV_NAME" ]; then
    echo -e "${YELLOW}Virtual environment $VENV_NAME does not exist. Creating it...${NC}"
    # Create the virtual environment
    $PYTHON_VERSION -m venv ".venv/$VENV_NAME"
    check_specific_exit_code $? "Create virtual environment"
fi

# Check for the existence of global_venv.pth in the site-packages directory
# Use find to handle potential python3.x variations more robustly #
SITE_PACKAGES_DIR=$(find ".venv/$VENV_NAME/lib/" -maxdepth 1 -type d -name 'python3*' -print -quit)/site-packages
check_specific_exit_code $? "Find site-packages directory"
if [ ! -f "$SITE_PACKAGES_DIR/global_venv.pth" ]; then
    echo -e "${YELLOW}Creating global_venv.pth file in $SITE_PACKAGES_DIR...${NC}"
    # Create the global_venv.pth file
    realpath ~/git/global_venv/.venv/GLOBAL/lib/$PYTHON_VERSION/site-packages >"$SITE_PACKAGES_DIR/global_venv.pth"
    check_specific_exit_code $? "Create global_venv.pth"
fi

# Check if the requirements.in file does not exist
if [ ! -f "requirements.in" ]; then
    echo -e "${YELLOW}requirements.in file does not exist. Creating it...${NC}"
    # Create a new requirements.in file
    touch requirements.in
    check_specific_exit_code $? "Create requirements.in"
fi

# Activate the virtual environment
echo -e "${CYAN}Activating the virtual environment...${NC}"
source ".venv/$VENV_NAME/bin/activate"
check_specific_exit_code $? "Activate virtual environment"

# Compile the requirements.in file and log the output
echo -e "${CYAN}Compiling requirements.in...${NC}"
# Execute the pipeline and capture the exit status of pip-compile (the first command) #
pip-compile requirements.in | tee -a "$REQUIREMENTS_LOG"
compile_status=${PIPESTATUS[0]} # Get exit code of pip-compile specifically #
# Check the captured exit status of pip-compile #
check_specific_exit_code $compile_status "pip-compile"

# Sync the requirements.txt file and log the output
echo -e "${CYAN}Syncing requirements.txt...${NC}"
# Execute the pipeline and capture the exit status of pip-sync #
pip-sync requirements.txt | tee -a "$REQUIREMENTS_LOG"
sync_status=${PIPESTATUS[0]} # Get exit code of pip-sync specifically #
# Check the captured exit status of pip-sync #
check_specific_exit_code $sync_status "pip-sync"

# Install from a nodeps.txt file if it exists
if [ -f "nodeps.txt" ]; then
    echo -e "${YELLOW}nodeps.txt file exists. Installing from it...${NC}"
    pip install --no-deps -r nodeps.txt
    check_specific_exit_code $? "Install from nodeps.txt" # Check exit code of pip install #
fi

# Generate a current dependency tree and save it to a file
echo -e "${CYAN}Generating current dependency tree...${NC}"
pipdeptree | egrep "^[a-z]" >pipdeptree_current.txt
check_specific_exit_code $? "Generate dependency tree" # Check exit code of the pipdeptree pipeline #

# Deactivate the virtual environment (optional but good practice) #
echo -e "${CYAN}Deactivating virtual environment...${NC}"
deactivate

cd - >/dev/null # Go back to the original directory silently #
check_specific_exit_code $? "Change back to original directory"

echo -e "${GREEN}Pip sync completed successfully.${NC}"
