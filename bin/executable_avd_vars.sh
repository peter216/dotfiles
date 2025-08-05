#!/usr/bin/bash

secrets="$(gopass cat "$1")"
eval "$(echo "$secrets" | jq -r 'to_entries|map("export \(.key)=\(.value|@sh)")|.[]')"
