#!/usr/bin/env bash

set -euo pipefail


############################################################
# Configuration
############################################################

CORES="${1:-8}"


echo
echo "============================================================"
echo " Microbiome Pipeline"
echo "============================================================"
echo "Cores: ${CORES}"
echo


############################################################
# STEP 1 — PREFLIGHT
############################################################

echo
echo ">>> STEP 1: PREFLIGHT VALIDATION"
echo

snakemake \
    --use-conda \
    --cores 1 \
    --rerun-incomplete \
    --forcerun preflight_validation \
    results/qc/preflight/preflight_validation.json


echo
echo ">>> PREFLIGHT PASSED"
echo


############################################################
# STEP 2 — DAG DRY-RUN
############################################################

echo
echo ">>> STEP 2: SNAKEMAKE DAG VALIDATION"
echo

snakemake \
    --dry-run \
    --printshellcmds \
    --use-conda \
    --cores "${CORES}"


echo
echo ">>> DAG VALIDATION PASSED"
echo


############################################################
# STEP 3 — FULL PIPELINE
############################################################

echo
echo ">>> STEP 3: FULL PIPELINE"
echo

snakemake \
    --use-conda \
    --cores "${CORES}" \
    --rerun-incomplete \
    --printshellcmds


echo
echo "============================================================"
echo " PIPELINE COMPLETED SUCCESSFULLY"
echo "============================================================"
echo