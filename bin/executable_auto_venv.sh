# Function: Walk up to find and activate nearest .venv, set PROJECT_NAME, and load .env
function auto_venv() {
    [[ $AUTOVENVOFF -eq 1 ]] && return
    local dir=$PWD
    # if Windows, use Scripts instead of bin
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        WIN=1
        subdir=Scripts
    else
        WIN=0
        subdir=bin
    fi
    [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}dir: $dir${RESET}"
    [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}subdir: $subdir${RESET}"
    while [ "$dir" != "/" ]; do
        if [[ $WIN -eq 1 ]]; then
          if [ -f $dir/.uv ]; then
            uvdir=$(cat $dir/.uv | tr -d '[:space:]')
          else
            dir=$(dirname "$dir")
            continue
          fi
        else
          uvdir=.uv
        fi
        if [ -f "$dir/$uvdir/.venv/$subdir/activate" ]; then
            [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}Found $uvdir/.venv in: $dir${RESET}"
            [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}VIRTUAL_ENV: $VIRTUAL_ENV${RESET}"
            if [ -d "$VIRTUAL_ENV" ]; then
                VENV_INODE=$(stat -c %i "$VIRTUAL_ENV")
                [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}VENV_INODE: $VENV_INODE${RESET}"
            else
                [[ $DEBUG -eq 1 ]] && echo -e "${YELLOW}No existing virtual environment found.${RESET}"
                VENV_INODE=""
            fi
            NEWFILE_INODE=$(stat -c %i "$dir/$uvdir/.venv")
            NEWFILE_REALPATH=$(realpath "$dir/$uvdir/.venv")
            [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}NEWFILE_INODE: $NEWFILE_INODE${RESET}"
            [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}NEWFILE_REALPATH: $NEWFILE_REALPATH${RESET}"
            if [[ "$VENV_INODE" == "$NEWFILE_INODE" ]]; then
                [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}Already in the correct virtual environment: $NEWFILE_REALPATH${RESET}"
                [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}Returning from auto_venv${RESET}"
                return
            else
                source "$dir/$uvdir/.venv/$subdir/activate" &&
                    echo -e "${GREEN}Activated virtual environment: $NEWFILE_REALPATH${RESET}"
                [[ $DEBUG -eq 1 ]] && echo -e "${YELLOW}python  : $(python --version | awk '{print $2}')${RESET}"
                TOML_FILE="$dir/$uvdir/pyproject.toml"
                if [ -f $TOML_FILE ]; then
                    [[ $DEBUG -eq 1 ]] && echo -e "${YELLOW}toml    : $TOML_FILE${RESET}"
                    export PROJECT_NAME=$(awk -F' *= *' '/^name *=/ { gsub(/"/, "", $2); print $2; exit }' $TOML_FILE)
                    [[ $DEBUG -eq 1 ]] && echo -e "${YELLOW}project : $PROJECT_NAME${RESET}"
                fi
                if [ -f $dir/.env ]; then
                    ENVFILE_REALPATH=$(realpath "$dir/.env")
                    [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}ENVFILE_REALPATH: $ENVFILE_REALPATH${RESET}"
                    source "$ENVFILE_REALPATH"
                    echo -e "${GREEN}Loaded environment variables from: $ENVFILE_REALPATH${RESET}"
                    [[ $DEBUG -eq 1 ]] && echo -e "${YELLOW}env${RESET}"
                    for var in $(grep -o "\S+=\S+" $dir/.env | grep -v '^#'); do
                        [[ $DEBUG -eq 1 ]] && echo -e "    - ${MAGENTA}$var${RESET}"
                    done
                fi
            fi
            [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}Returning from auto_venv${RESET}"
            return
        else
            [[ $DEBUG2 -eq 1 ]] && echo -e "${CYAN}dir: $dir${RESET}"
        fi
        dir=$(dirname "$dir")
    done
    [[ $DEBUG -eq 1 ]] && echo -e "${MAGENTA}auto_venv finished without finding $uvdir/.venv${RESET}"
}
