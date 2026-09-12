BATCH_CORRECTION_ENABLED = bool(
    config["batch_correction"]["enabled"]
)

BATCH_CORRECTION_METHOD = str(
    config["batch_correction"]["method"]
).lower()


if BATCH_CORRECTION_METHOD not in {
    "combat",
    "mmuphin"
}:
    raise ValueError(
        "batch_correction.method must be "
        "'combat' or 'mmuphin'."
    )


############################################################
# Select canonical corrected CLR table
############################################################

def get_batch_corrected_source(wildcards):

    if not BATCH_CORRECTION_ENABLED:

        return (
            "results/batch_effect/"
            "feature_table_clr.tsv"
        )

    if BATCH_CORRECTION_METHOD == "combat":

        return (
            "results/batch_effect/corrected/"
            "combat/feature_table_corrected_clr.tsv"
        )

    return (
        "results/batch_effect/corrected/"
        "mmuphin/feature_table_corrected_clr.tsv"
    )


############################################################
# ComBat branch
#
# CLR -> ComBat -> corrected CLR
############################################################

rule combat_batch_correction:

    input:

        table=
            "results/batch_effect/feature_table_clr.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:

        table=
            "results/batch_effect/corrected/"
            "combat/feature_table_corrected_clr.tsv"

    params:

        batch=
            config["batch_correction"]["batch_variable"],

        group=
            config["batch_correction"]["biological_variable"]

    log:

        "logs/batch_effect/combat_correction.log"

    benchmark:

        "benchmark/batch_effect/combat_correction.txt"

    conda:

        "envs/r_batch.yaml"

    shell:

        r"""
        set -euo pipefail

        mkdir -p "$(dirname "{output.table}")"
        mkdir -p "$(dirname "{log}")"
        mkdir -p "$(dirname "{benchmark}")"

        Rscript scripts/R/combat_correction.R \
            "{input.table}" \
            "{input.metadata}" \
            "{params.batch}" \
            "{params.group}" \
            "{output.table}" \
            > "{log}" 2>&1
        """


############################################################
# MMUPHin branch
#
# FILTERED COUNTS -> MMUPHin adjusted abundance
############################################################

rule mmuphin_batch_correction:

    input:

        table=
            "results/filtering/feature_table_filtered.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:

        abundance=
            "results/batch_effect/corrected/mmuphin/"
            "feature_table_adjusted_abundance.tsv",

        diagnostic=
            "results/batch_effect/corrected/mmuphin/"
            "mmuphin_diagnostic.pdf",

        summary=
            "results/batch_effect/corrected/mmuphin/"
            "mmuphin_summary.tsv"

    params:

        batch=
            config["batch_correction"]["batch_variable"],

        group=
            config["batch_correction"]["biological_variable"]

    log:

        "logs/batch_effect/mmuphin_correction.log"

    benchmark:

        "benchmark/batch_effect/mmuphin_correction.txt"

    conda:

        "envs/r_batch.yaml"

    shell:

        r"""
        set -euo pipefail

        mkdir -p results/batch_effect/corrected/mmuphin
        mkdir -p "$(dirname "{log}")"
        mkdir -p "$(dirname "{benchmark}")"

        Rscript scripts/R/mmuphin_correction.R \
            "{input.table}" \
            "{input.metadata}" \
            "{params.batch}" \
            "{params.group}" \
            "{output.abundance}" \
            "{output.diagnostic}" \
            "{output.summary}" \
            > "{log}" 2>&1
        """


############################################################
# Zero replacement AFTER MMUPHin
############################################################

rule mmuphin_zero_replacement:

    input:

        "results/batch_effect/corrected/mmuphin/"
        "feature_table_adjusted_abundance.tsv"

    output:

        "results/batch_effect/corrected/mmuphin/"
        "feature_table_adjusted_zero_replaced.tsv"

    log:

        "logs/batch_effect/mmuphin_zero_replacement.log"

    benchmark:

        "benchmark/batch_effect/mmuphin_zero_replacement.txt"

    conda:

        "envs/r_selbal.yaml"

    shell:

        r"""
        set -euo pipefail

        Rscript scripts/R/zero_replacement.R \
            "{input}" \
            "{output}" \
            > "{log}" 2>&1
        """


############################################################
# CLR AFTER MMUPHin
############################################################

rule mmuphin_clr_normalization:

    input:

        "results/batch_effect/corrected/mmuphin/"
        "feature_table_adjusted_zero_replaced.tsv"

    output:

        "results/batch_effect/corrected/mmuphin/"
        "feature_table_corrected_clr.tsv"

    log:

        "logs/batch_effect/mmuphin_clr.log"

    benchmark:

        "benchmark/batch_effect/mmuphin_clr.txt"

    conda:

        "envs/r_batch.yaml"

    shell:

        r"""
        set -euo pipefail

        Rscript scripts/R/clr_normalization.R \
            "{input}" \
            "{output}" \
            > "{log}" 2>&1
        """


############################################################
# Canonical output
#
# Downstream rules ALWAYS receive CLR regardless of method.
############################################################

rule batch_correction:

    input:

        source=get_batch_corrected_source

    output:

        table=
            "results/batch_effect/corrected/"
            "feature_table_corrected.tsv"

    log:

        "logs/batch_effect/batch_correction_select.log"

    benchmark:

        "benchmark/batch_effect/batch_correction_select.txt"

    shell:

        r"""
        set -euo pipefail

        mkdir -p "$(dirname "{output.table}")"
        mkdir -p "$(dirname "{log}")"
        mkdir -p "$(dirname "{benchmark}")"

        cp \
            "{input.source}" \
            "{output.table}"

        echo "Batch correction enabled: {BATCH_CORRECTION_ENABLED}" \
            > "{log}"

        echo "Batch correction method: {BATCH_CORRECTION_METHOD}" \
            >> "{log}"

        echo "Selected source: {input.source}" \
            >> "{log}"
        """