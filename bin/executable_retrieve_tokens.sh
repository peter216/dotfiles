#!/usr/bin/env bash
# This script is a quick way to retrieve secrets from gopass

VALUES_ONLY=0
DEBUG=0
RAW_OUTPUT=0
FLAGS=""

usage() {
  BASENAME=$(basename "$0")
  echo
  echo "Usage: $BASENAME [-v] [-d] [-r] -n <variable_name> -k <keys>"
  echo "  -n <variable_name>: Name of the gopass variable to retrieve"
  echo "  -k <keys>: Comma-separated list of keys to retrieve from the variable"
  echo "  -v: Output only values, not keys"
  echo "  -r: Output raw values (no quotes)"
  echo "  -d: Enable debug mode"
  echo "  -h: Show this help message"
  echo
  echo "Examples:"
  echo "  $BASENAME -n .env-vars -k POSTMAN_API_TOKEN"
  echo "  $BASENAME -d -v -r -n .env-vars -k MPDEVTOKEN,MPPRODTOKEN"
  echo
  exit 1
}

# Get cli arguments
while getopts "vdrhn:k:" opt; do
  case $opt in
    n) VARNAME="$OPTARG"
    ;;
    k) INPUT_KEYS="$OPTARG"
    ;;
    v) VALUES_ONLY=1
    ;;
    d) DEBUG=1
    ;;
    r) RAW_OUTPUT=1
    ;;
    h) usage
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

# Split into a list by commas
IFS=',' read -r -a KEYS_ARRAY <<< "$INPUT_KEYS"
[[ $DEBUG -eq 1 ]] && echo "DEBUG: Input keys: ${KEYS_ARRAY[*]}"

if [[ $VALUES_ONLY == 1 ]]; then
  # Join the keys with a dot for jq
  # Example: '.MPDEVTOKEN, .MPPRODTOKEN'
  KEYS=$(printf '.%s,' "${KEYS_ARRAY[@]}" | sed 's/,$//')
  [[ $DEBUG -eq 1 ]] && echo "DEBUG: jq keys (dot notation): ${KEYS}"
else
  # Example: '[]'
  [[ $DEBUG -eq 1 ]] && echo "Number of keys: ${#KEYS_ARRAY[@]}"
  # Output first key
  [[ $DEBUG -eq 1 ]] && echo "DEBUG: First key: ${KEYS_ARRAY[0]}"
  if [[ ${#KEYS_ARRAY[@]} -eq 0 || -z ${KEYS_ARRAY[0]} || ${KEYS_ARRAY[0]} == "[]" ]]; then
    KEYS='.'
    [[ $DEBUG -eq 1 ]] && echo "DEBUG: No keys provided, using default: ${KEYS}"
  else
    # Join the keys with commas for jq brace notation
    # Example: '{MPDEVTOKEN, MPPRODTOKEN}'
    KEYS=$(printf '{%s}' "$(echo "${KEYS_ARRAY[@]}" | sed 's/ /,/')")
    [[ $DEBUG -eq 1 ]] && echo "DEBUG: jq keys (brace notation): ${KEYS}"
  fi
fi
if [[ $RAW_OUTPUT -eq 1 ]]; then
  FLAGS="$FLAGS --raw-output"
fi
CMD="gopass cat ${VARNAME} | jq ${FLAGS} '${KEYS}'"
[[ $DEBUG -eq 1 ]] && echo "DEBUG: Executing command: $CMD"
eval "$CMD"
