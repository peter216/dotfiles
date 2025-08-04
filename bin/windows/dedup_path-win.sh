# Optimized dedup_path function
function dedup_path() {
    local old_path="$PATH"
    local new_path=""
    declare -A path_seen

    # Deduplicate PATH using an associative array
    IFS=':' read -ra path_parts <<<"$old_path"
    for part in "${path_parts[@]}"; do
        if [[ -n "$part" && -z "${path_seen[$part]}" ]]; then
            path_seen["$part"]=1
            new_path+="$part:"
        fi
    done

    # Remove trailing colon
    PATH="${new_path%:}"
    export PATH
}
