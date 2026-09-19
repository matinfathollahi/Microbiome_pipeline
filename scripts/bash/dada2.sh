#!/usr/bin/env bash

set -Eeuo pipefail

########################################
# Usage
########################################
if [[ $# -ne 15 ]]; then
    cat <<EOF
Usage:
$0 DEMUX TABLE REPSEQ STATS THREADS \
   TRIM_LEFT_F TRIM_LEFT_R \
   TRUNC_LEN_F TRUNC_LEN_R \
   MAX_EE_F MAX_EE_R \
   TRUNC_Q CHIMERA POOLING
EOF
    exit 1
fi

########################################
# Input arguments
########################################
DEMUX="$1"
TABLE="$2"
REPSEQ="$3"
STATS="$4"

THREADS="$5"

TRIM_LEFT_F="$6"
TRIM_LEFT_R="$7"

TRUNC_LEN_F="$8"
TRUNC_LEN_R="$9"

MAX_EE_F="${10}"
MAX_EE_R="${11}"

TRUNC_Q="${12}"

CHIMERA="${13}"
POOLING="${14}"
MIN_OVERLAP="${15}"

########################################
# Error handler
########################################
trap 'echo "[ERROR] Script failed at line $LINENO." >&2' ERR

########################################
# Check dependencies
########################################
if ! command -v qiime >/dev/null 2>&1; then
    echo "[ERROR] qiime is not installed or not in PATH."
    exit 1
fi

########################################
# Check input artifact
########################################
if [[ ! -f "$DEMUX" ]]; then
    echo "[ERROR] Input artifact not found:"
    echo "        $DEMUX"
    exit 1
fi

########################################
# Validate THREADS
########################################
if ! [[ "$THREADS" =~ ^[0-9]+$ ]]; then
    echo "[ERROR] THREADS must be a positive integer."
    exit 1
fi

if (( THREADS < 1 )); then
    echo "[ERROR] THREADS must be at least 1."
    exit 1
fi

########################################
# Validate chimera method
########################################
case "$CHIMERA" in
    consensus|pooled|none)
        ;;
    *)
        echo "[ERROR] Invalid chimera method: $CHIMERA"
        echo "Allowed values:"
        echo "  consensus"
        echo "  pooled"
        echo "  none"
        exit 1
        ;;
esac

########################################
# Validate pooling method
########################################
case "$POOLING" in
    independent|pseudo)
        ;;
    *)
        echo "[ERROR] Invalid pooling method: $POOLING"
        echo "Allowed values:"
        echo "  independent"
        echo "  pseudo"
        exit 1
        ;;
esac



########################################
# Validate minimum overlap
########################################
if ! [[ "$MIN_OVERLAP" =~ ^[0-9]+$ ]]; then
    echo "[ERROR] MIN_OVERLAP must be an integer."
    exit 1
fi

if (( MIN_OVERLAP < 4 )); then
    echo "[ERROR] MIN_OVERLAP must be at least 4."
    exit 1
fi

########################################
# Create output directories
########################################
mkdir -p "$(dirname "$TABLE")"
mkdir -p "$(dirname "$REPSEQ")"
mkdir -p "$(dirname "$STATS")"

BASE_STATS="$(dirname "$STATS")/base_transition_stats.qza"

########################################
# Print configuration
########################################
echo "==========================================="
echo "Running DADA2"
echo "==========================================="
echo "QIIME version : $(qiime --version)"
echo "Input         : $DEMUX"
echo "Table         : $TABLE"
echo "RepSeq        : $REPSEQ"
echo "Stats         : $STATS"
echo "Threads       : $THREADS"
echo "Trim left F   : $TRIM_LEFT_F"
echo "Trim left R   : $TRIM_LEFT_R"
echo "Trunc len F   : $TRUNC_LEN_F"
echo "Trunc len R   : $TRUNC_LEN_R"
echo "MaxEE F       : $MAX_EE_F"
echo "MaxEE R       : $MAX_EE_R"
echo "TruncQ        : $TRUNC_Q"
echo "Chimera       : $CHIMERA"
echo "Pooling       : $POOLING"
echo "Min overlap   : $MIN_OVERLAP"
echo "Started       : $(date)"
echo "==========================================="

########################################
# Run DADA2
########################################
qiime dada2 denoise-paired \
    --i-demultiplexed-seqs "$DEMUX" \
    --p-trim-left-f "$TRIM_LEFT_F" \
    --p-trim-left-r "$TRIM_LEFT_R" \
    --p-trunc-len-f "$TRUNC_LEN_F" \
    --p-trunc-len-r "$TRUNC_LEN_R" \
    --p-max-ee-f "$MAX_EE_F" \
    --p-max-ee-r "$MAX_EE_R" \
    --p-trunc-q "$TRUNC_Q" \
    --p-chimera-method "$CHIMERA" \
    --p-pooling-method "$POOLING" \
    --p-min-overlap "$MIN_OVERLAP" \
    --p-n-threads "$THREADS" \
    --o-table "$TABLE" \
    --o-representative-sequences "$REPSEQ" \
    --o-denoising-stats "$STATS" \
    --o-base-transition-stats "$BASE_STATS"

########################################
# Finished
########################################
echo "==========================================="
echo "DADA2 completed successfully."
echo "Finished: $(date)"
echo "==========================================="