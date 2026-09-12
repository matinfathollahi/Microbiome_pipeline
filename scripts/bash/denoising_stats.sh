#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <input> <output.qzv>"
    exit 1
fi

INPUT="$1"
OUTPUT="$2"

command -v qiime >/dev/null || {
    echo "Error: qiime is not installed or not in PATH."
    exit 1
}

[[ -f "$INPUT" ]] || {
    echo "Error: Input file '$INPUT' not found."
    exit 1
}

mkdir -p "$(dirname "$OUTPUT")"

qiime metadata tabulate \
    --m-input-file "$INPUT" \
    --o-visualization "$OUTPUT"

echo "Visualization saved to: $OUTPUT"