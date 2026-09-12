#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 8 ]]; then
    echo "Usage:"
    echo "$0 <feature_table> <taxonomy> <metadata> <output_dir> <class_column> <normalization> <alpha> <lda_threshold>"
    exit 1
fi

TABLE="$1"
TAXONOMY="$2"
METADATA="$3"
OUTDIR="$4"
CLASS_COLUMN="$5"
NORMALIZATION="$6"
ALPHA="$7"
LDA_THRESHOLD="$8"

mkdir -p "$OUTDIR"

LEFSE_TABLE="$OUTDIR/lefse_input.tsv"
LEFSE_INPUT="$OUTDIR/lefse_input.in"

RAW_RESULTS="$OUTDIR/lefse_results.res"

SIGNIFICANT="$OUTDIR/significant_taxa.tsv"

ABUNDANCE="$OUTDIR/feature_abundance.tsv"

MAPPING="$OUTDIR/feature_mapping.tsv"


if ! command -v lefse_format_input.py >/dev/null 2>&1; then
    echo "Error: lefse_format_input.py not found."
    exit 1
fi

if ! command -v lefse_run.py >/dev/null 2>&1; then
    echo "Error: lefse_run.py not found."
    exit 1
fi


echo "Preparing LEfSe input..."

python scripts/python/prepare_lefse_input.py \
    --table "$TABLE" \
    --metadata "$METADATA" \
    --class-column "$CLASS_COLUMN" \
    --lefse-table "$LEFSE_TABLE" \
    --abundance "$ABUNDANCE" \
    --mapping "$MAPPING"


echo "Formatting LEfSe input..."

lefse_format_input.py \
    "$LEFSE_TABLE" \
    "$LEFSE_INPUT" \
    -c 1 \
    -o "$NORMALIZATION"


echo "Running LEfSe..."

lefse_run.py \
    "$LEFSE_INPUT" \
    "$RAW_RESULTS" \
    -a "$ALPHA" \
    -w "$ALPHA" \
    -l "$LDA_THRESHOLD"


echo "Parsing LEfSe results..."

python scripts/python/parse_lefse_results.py \
    --results "$RAW_RESULTS" \
    --mapping "$MAPPING" \
    --taxonomy "$TAXONOMY" \
    --output "$SIGNIFICANT"


if [[ ! -f "$SIGNIFICANT" ]]; then
    echo "Error: significant_taxa.tsv was not created."
    exit 1
fi

echo "LEfSe completed successfully."
echo "Results: $SIGNIFICANT"