#!/usr/bin/env bash

set -Eeuo pipefail

########################################
# Functions
########################################

error() {
    echo "[ERROR] $*" >&2
    exit 1
}

log() {
    echo "[INFO] $*"
}

########################################
# Check arguments
########################################

if [[ $# -ne 4 ]]; then
    cat <<EOF
Usage:
    $0 <input.sra> <output_dir> <threads> <temp_dir>

Example:
    $0 SRR123456.sra fastq 8 tmp
EOF
    exit 1
fi

########################################
# Input variables
########################################

SRA_FILE="$1"
OUTDIR="$2"
THREADS="$3"
TEMPDIR="$4"

########################################
# Dependency check
########################################

command -v fasterq-dump >/dev/null 2>&1 \
    || error "fasterq-dump is not installed or not in PATH."

########################################
# Validate input
########################################

[[ -f "$SRA_FILE" ]] \
    || error "Input SRA file not found: $SRA_FILE"

[[ "$THREADS" =~ ^[1-9][0-9]*$ ]] \
    || error "THREADS must be a positive integer."

mkdir -p "$OUTDIR"
mkdir -p "$TEMPDIR"

ACCESSION=$(basename "$SRA_FILE" .sra)

log "Input      : $SRA_FILE"
log "Accession  : $ACCESSION"
log "Output Dir : $OUTDIR"
log "Threads    : $THREADS"
log "Temp Dir   : $TEMPDIR"

########################################
# Convert SRA -> FASTQ
########################################

fasterq-dump \
    "$SRA_FILE" \
    --split-files \
    --threads "$THREADS" \
    --temp "$TEMPDIR" \
    --outdir "$OUTDIR"

########################################
# Check output
# Pipeline supports paired-end data only
########################################

R1="${OUTDIR}/${ACCESSION}_1.fastq"
R2="${OUTDIR}/${ACCESSION}_2.fastq"
SE="${OUTDIR}/${ACCESSION}.fastq"

if [[ -s "$R1" && -s "$R2" ]]; then

    log "Paired-end FASTQ generated successfully."
    log "R1: $R1"
    log "R2: $R2"

elif [[ -s "$SE" ]]; then

    error "Accession ${ACCESSION} produced single-end FASTQ (${SE}). This pipeline supports paired-end sequencing only."

elif [[ -s "$R1" && ! -s "$R2" ]]; then

    error "Accession ${ACCESSION} produced only R1 (${R1}) but no valid R2. This pipeline requires paired-end reads."

elif [[ -s "$R2" && ! -s "$R1" ]]; then

    error "Accession ${ACCESSION} produced only R2 (${R2}) but no valid R1. This pipeline requires paired-end reads."

else

    error "FASTQ generation failed for ${ACCESSION}. Expected non-empty paired-end files: ${R1} and ${R2}."

fi

########################################
# Summary
########################################

log "Conversion completed successfully."