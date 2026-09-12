#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <rep-seqs.qza> <output.qzv>"
    exit 1
fi

REPSEQ="$1"
OUTPUT="$2"

if [ ! -f "$REPSEQ" ]; then
    echo "Error: input file not found: $REPSEQ"
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

qiime feature-table tabulate-seqs \
    --i-data "$REPSEQ" \
    --o-visualization "$OUTPUT"

echo "Done: $OUTPUT"