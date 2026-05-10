#!/usr/bin/env bash
#
# Script to check for formatters/*.yaml entries that have no corresponding event
# data class DATA_TYPE.

EXIT_FAILURE=1
EXIT_SUCCESS=0

set -e

FORMATTERS_DIRECTORY="plaso/data/formatters"

if [[ ! -d "${FORMATTERS_DIRECTORY}" ]];
then
    echo "Missing: ${FORMATTERS_DIRECTORY}"
    exit ${EXIT_FAILURE}
fi

declare -a formatter_entries=()

while IFS= read -r line;
do
    formatter_entries+=("$line")
done < <(awk '
    /^[[:space:]]*data_type[[:space:]]*:/ {
        gsub(/.*data_type[[:space:]]*:[[:space:]]*'\''/, "", $0)
        gsub(/'\''[[:space:]]*$/, "", $0)
        gsub(/"[[:space:]]*$/, "", $0)
        gsub(/^"/, "", $0)
        if ($0 != "") print $0
    }
' ${FORMATTERS_DIRECTORY}/*.yaml 2>/dev/null | sort -u)

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

declare -a missing_entries=()

for entry in "${source_entries[@]}";
do
    if [[ -z "${formatter_entries[$entry]}" ]];
    then
        missing_entries+=("$entry")
    fi
done

declare -a unused_entries=()

for entry in "${formatter_entries[@]}";
do
    if [[ -z "${source_entries[$entry]}" ]];
    then
        unused_entries+=("$entry")
    fi
done

if [[ ${#unused_entries[@]} -ne 0 ]];
then
    echo "Unused formatter helper entries:"

    for entry in "${unused_entries[@]}";
    do
        echo "- ${entry}"
    done
    exit ${EXIT_FAILURE}
fi

if [[ ${#missing_entries[@]} -ne 0 ]];
then
    echo "Missing formatter helper entries:"

    for entry in "${missing_entries[@]}";
    do
        echo "- ${entry}"
    done
    exit ${EXIT_FAILURE}
fi

exit ${EXIT_SUCCESS}
