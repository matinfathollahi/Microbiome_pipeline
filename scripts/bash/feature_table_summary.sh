#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <table.qza> <metadata.tsv> <output.qzv>"
    exit 1
fi

TABLE="$1"
METADATA="$2"
OUTPUT="$3"

[[ -f "$TABLE" ]] || { echo "Error: Table not found: $TABLE"; exit 1; }
[[ -f "$METADATA" ]] || { echo "Error: Metadata not found: $METADATA"; exit 1; }

mkdir -p "$(dirname "$OUTPUT")"

qiime feature-table summarize \
    --i-table "$TABLE" \
    --m-sample-metadata-file "$METADATA" \
    --o-visualization "$OUTPUT"

echo "Summary saved to: $OUTPUT"