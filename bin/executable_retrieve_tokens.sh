#!/usr/bin/env bash
# This script is a quick way to retrieve secrets from gopass

VALUES_ONLY=0
DEBUG=0
RAW_OUTPUT=0
FLAGS=""

# Get cli arguments
while getopts "vdrn:k:" opt; do
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
  # Example: '{MPDEVTOKEN, MPPRODTOKEN}'
  KEYS=$(printf '{%s}' "$(echo "${KEYS_ARRAY[@]}" | sed 's/ /,/')")
  [[ $DEBUG -eq 1 ]] && echo "DEBUG: jq keys (brace notation): ${KEYS}"
fi
if [[ $RAW_OUTPUT -eq 1 ]]; then
  FLAGS="$FLAGS --raw-output"
fi
CMD="gopass cat ${VARNAME} | jq ${FLAGS} '${KEYS}'"
[[ $DEBUG -eq 1 ]] && echo "DEBUG: Executing command: $CMD"
eval "$CMD"
