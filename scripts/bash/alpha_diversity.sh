#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <alpha.qza> <metadata.tsv> <output.qzv>"
    exit 1
fi

ALPHA="$1"
METADATA="$2"
OUTPUT="$3"

[[ -f "$ALPHA" ]] || { echo "Error: $ALPHA not found."; exit 1; }
[[ -f "$METADATA" ]] || { echo "Error: $METADATA not found."; exit 1; }

mkdir -p "$(dirname "$OUTPUT")"

qiime diversity alpha-group-significance \
    --i-alpha-diversity "$ALPHA" \
    --m-metadata-file "$METADATA" \
    --o-visualization "$OUTPUT"

echo "Done: $OUTPUT"