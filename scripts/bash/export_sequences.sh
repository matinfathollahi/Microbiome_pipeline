#!/usr/bin/env bash

set -euo pipefail

# Check arguments
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <input.qza|input.qzv> <output_directory>"
    exit 1
fi

INPUT="$1"
OUTDIR="$2"

# Check that input file exists
if [[ ! -f "$INPUT" ]]; then
    echo "Error: Input file '$INPUT' does not exist."
    exit 1
fi

# Create output directory if needed
mkdir -p "$OUTDIR"

# Export QIIME 2 artifact
qiime tools export \
    --input-path "$INPUT" \
    --output-path "$OUTDIR"

echo "Export completed successfully."