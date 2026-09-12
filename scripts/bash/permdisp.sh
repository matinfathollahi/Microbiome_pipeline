#!/usr/bin/env bash

set -euo pipefail

# Check number of arguments
if [[ $# -ne 6 ]]; then
    echo "Usage: $0 <distance> <metadata> <output> <column> <permutations> <pairwise>"
    echo
    echo "Arguments:"
    echo "  distance       Path to distance matrix (.qza)"
    echo "  metadata       Path to metadata file"
    echo "  output         Output visualization (.qzv)"
    echo "  column         Metadata column"
    echo "  permutations   Number of permutations (integer)"
    echo "  pairwise       true | false"
    exit 1
fi

DISTANCE="$1"
METADATA="$2"
OUTPUT="$3"
COLUMN="$4"
PERMUTATIONS="$5"
PAIRWISE="$6"

# Check input files
[[ -f "$DISTANCE" ]] || {
    echo "Error: Distance matrix not found: $DISTANCE" >&2
    exit 1
}

[[ -f "$METADATA" ]] || {
    echo "Error: Metadata file not found: $METADATA" >&2
    exit 1
}

# Validate permutations
[[ "$PERMUTATIONS" =~ ^[0-9]+$ ]] || {
    echo "Error: PERMUTATIONS must be a positive integer." >&2
    exit 1
}

# Validate pairwise argument
case "$PAIRWISE" in
    true|false)
        ;;
    *)
        echo "Error: PAIRWISE must be 'true' or 'false'." >&2
        exit 1
        ;;
esac

# Create output directory if needed
mkdir -p "$(dirname "$OUTPUT")"

# Build QIIME command
CMD=(
    qiime diversity beta-group-significance
    --i-distance-matrix "$DISTANCE"
    --m-metadata-file "$METADATA"
    --m-metadata-column "$COLUMN"
    --p-method permdisp
    --p-permutations "$PERMUTATIONS"
    --o-visualization "$OUTPUT"
)

# Enable pairwise comparisons if requested
if [[ "$PAIRWISE" == "true" ]]; then
    CMD+=(--p-pairwise)
fi

# Print command (optional, useful for debugging)
echo "Running:"
printf '%q ' "${CMD[@]}"
echo

# Execute command
"${CMD[@]}"

echo "Done."