#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 6 ]; then
    echo "Usage: $0 <distance> <metadata> <output> <column> <permutations> <pairwise>"
    exit 1
fi

DISTANCE=$1
METADATA=$2
OUTPUT=$3
COLUMN=$4
PERMUTATIONS=$5
PAIRWISE=$6

command -v qiime >/dev/null 2>&1 || {
    echo "Error: qiime not found in PATH."
    exit 1
}

[[ -f "$DISTANCE" ]] || {
    echo "Distance matrix not found: $DISTANCE"
    exit 1
}

[[ -f "$METADATA" ]] || {
    echo "Metadata file not found: $METADATA"
    exit 1
}

[[ "$PERMUTATIONS" =~ ^[0-9]+$ ]] || {
    echo "PERMUTATIONS must be an integer"
    exit 1
}

case "$PAIRWISE" in
    true|false) ;;
    *)
        echo "PAIRWISE must be true or false"
        exit 1
        ;;
esac

mkdir -p "$(dirname "$OUTPUT")"

CMD=(
    qiime diversity beta-group-significance
    --i-distance-matrix "$DISTANCE"
    --m-metadata-file "$METADATA"
    --m-metadata-column "$COLUMN"
    --p-method permanova
    --p-permutations "$PERMUTATIONS"
    --o-visualization "$OUTPUT"
)

if [[ "$PAIRWISE" == "true" ]]; then
    CMD+=(--p-pairwise)
fi

"${CMD[@]}"