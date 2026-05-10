#!/usr/bin/env bash
#
# Script to check for timeliner.yaml entries that have no corresponding event
# data class DATA_TYPE.

EXIT_FAILURE=1
EXIT_SUCCESS=0

set -e

TIMELINER_YAML="plaso/data/timeliner.yaml"

if [[ ! -f "${TIMELINER_YAML}" ]];
then
    echo "Missing: ${TIMELINER_YAML}"
    exit ${EXIT_FAILURE}
fi

declare -a timeliner_entries=()

while IFS= read -r line;
do
    timeliner_entries+=("$line")
done < <(awk '
    /^[[:space:]]*data_type[[:space:]]*:/ {
        gsub(/.*data_type[[:space:]]*:[[:space:]]*'\''/, "", $0)
        gsub(/'\''[[:space:]]*$/, "", $0)
        gsub(/"[[:space:]]*$/, "", $0)
        gsub(/^"/, "", $0)
        if ($0 != "") print $0
    }
' "${TIMELINER_YAML}" 2>/dev/null)

declare -A source_entries=()

while IFS= read -r line;
do
    if [[ -n "$line" ]];
    then
        source_entries["$line"]=1
    fi
done < <(grep -rh "DATA_TYPE = " "plaso" --include="*.py" \
    | sed "s/.*DATA_TYPE = ['\"]//;s/['\"].*//" \
    | sort -u)

declare -a unused_entries=()

for entry in "${timeliner_entries[@]}";
do
    if [[ -z "${source_entries[$entry]}" ]];
    then
        unused_entries+=("$entry")
    fi
done

total_count=${#timeliner_entries[@]}
unused_count=${#unused_entries[@]}
used_count=$((total_count - unused_count))

if [[ ${unused_count} -ne 0 ]];
then
    echo "Found unused timeliner.yaml entries:"

    for entry in "${unused_entries[@]}";
    do
        echo "- ${entry}"
    done
    exit ${EXIT_FAILURE}
fi

exit ${EXIT_SUCCESS}
