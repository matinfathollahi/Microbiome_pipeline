#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <input.qza|.qzv> <output_directory>"
    exit 1
fi

INPUT=$1
OUTDIR=$2

command -v qiime >/dev/null 2>&1 || {
    echo "Error: qiime command not found."
    exit 1
}

[[ -e "$INPUT" ]] || {
    echo "Error: Input file '$INPUT' does not exist."
    exit 1
}

mkdir -p "$OUTDIR"

qiime tools export \
    --input-path "$INPUT" \
    --output-path "$OUTDIR"

echo "Export completed successfully."