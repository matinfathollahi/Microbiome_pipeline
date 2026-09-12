#!/usr/bin/env bash

set -euo pipefail

# Check arguments
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <input> <output>" >&2
    exit 1
fi

INPUT="$1"
OUTPUT="$2"

# Check input file exists
if [[ ! -f "$INPUT" ]]; then
    echo "Error: Input file '$INPUT' does not exist." >&2
    exit 1
fi

# Create output directory if needed
mkdir -p "$(dirname "$OUTPUT")"

# Copy file
cp "$INPUT" "$OUTPUT"

echo "File copied successfully:"
echo "  From: $INPUT"
echo "  To:   $OUTPUT"