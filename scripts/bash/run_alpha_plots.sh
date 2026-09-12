#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <alpha_dir> <metadata.tsv> <output_dir>"
    exit 1
fi

ALPHA_DIR="$1"
METADATA="$2"
OUTPUT_DIR="$3"

R_SCRIPT="scripts/R/alpha_plots.R"

if [[ ! -f "$R_SCRIPT" ]]; then
    echo "Error: R script not found: $R_SCRIPT"
    exit 1
fi

if [[ ! -d "$ALPHA_DIR" ]]; then
    echo "Error: Alpha directory not found: $ALPHA_DIR"
    exit 1
fi

if [[ ! -f "$METADATA" ]]; then
    echo "Error: Metadata file not found: $METADATA"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

Rscript "$R_SCRIPT" \
    "$ALPHA_DIR" \
    "$METADATA" \
    "$OUTPUT_DIR"

echo "Alpha diversity plots completed successfully."