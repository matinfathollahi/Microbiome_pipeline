#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <alpha_vector.qza> <output_directory>"
    exit 1
fi

INPUT="$1"
OUTPUT="$2"

if ! command -v qiime >/dev/null 2>&1; then
    echo "Error: qiime is not installed or not in PATH."
    exit 1
fi

if [[ ! -f "$INPUT" ]]; then
    echo "Error: Input file '$INPUT' does not exist."
    exit 1
fi

if [[ "$INPUT" != *.qza ]]; then
    echo "Error: Input must be a .qza alpha diversity vector."
    exit 1
fi

mkdir -p "$OUTPUT"

qiime tools export \
    --input-path "$INPUT" \
    --output-path "$OUTPUT"

EXPECTED="$OUTPUT/alpha-diversity.tsv"

if [[ ! -f "$EXPECTED" ]]; then
    echo "Error: Expected alpha-diversity.tsv was not created."
    exit 1
fi

echo "Alpha diversity exported successfully:"
echo "$EXPECTED"