#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <distance.qza> <metadata.tsv> <output.qzv>"
    exit 1
fi

DISTANCE=$1
METADATA=$2
OUTPUT=$3

[[ -f "$DISTANCE" ]] || { echo "Error: Distance matrix not found."; exit 1; }
[[ -f "$METADATA" ]] || { echo "Error: Metadata file not found."; exit 1; }

command -v qiime >/dev/null 2>&1 || {
    echo "Error: qiime command not found."
    exit 1
}

mkdir -p "$(dirname "$OUTPUT")"

qiime diversity beta-group-significance \
    --i-distance-matrix "$DISTANCE" \
    --m-metadata-file "$METADATA" \
    --p-method permanova \
    --p-pairwise \
    --o-visualization "$OUTPUT"

echo "Done: $OUTPUT"