#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 6 ]; then
    echo "Usage: $0 <rep-seqs.qza> <classifier.qza> <output.qza> <threads> <batch-size> <confidence>"
    exit 1
fi

REPSEQ="$1"
CLASSIFIER="$2"
OUTPUT="$3"
THREADS="$4"
BATCH="$5"
CONFIDENCE="$6"

for f in "$REPSEQ" "$CLASSIFIER"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: File not found: $f"
        exit 1
    fi
done

mkdir -p "$(dirname "$OUTPUT")"

qiime feature-classifier classify-sklearn \
    --i-classifier "$CLASSIFIER" \
    --i-reads "$REPSEQ" \
    --p-n-jobs "$THREADS" \
    --p-reads-per-batch "$BATCH" \
    --p-confidence "$CONFIDENCE" \
    --o-classification "$OUTPUT"