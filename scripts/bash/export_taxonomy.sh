#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $0 <input.qza|input.qzv> <output_directory>"
    exit 1
}

# Check arguments
if [[ $# -ne 2 ]]; then
    usage
fi

INPUT="$1"
OUTDIR="$2"

# Check QIIME 2 installation
if ! command -v qiime >/dev/null 2>&1; then
    echo "Error: 'qiime' command not found. Please activate your QIIME 2 environment."
    exit 1
fi

# Check input file
if [[ ! -f "$INPUT" ]]; then
    echo "Error: Input file '$INPUT' does not exist."
    exit 1
fi

# Create output directory
mkdir -p "$OUTDIR"

echo "Exporting '$INPUT' to '$OUTDIR'..."

qiime tools export \
    --input-path "$INPUT" \
    --output-path "$OUTDIR"

echo "Export completed successfully."