rule predictive_mmuphin_sensitivity:
    input:
        table=
            "results/filtering/feature_table_filtered.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:
        table=
            "results/batch_effect/predictive/mmuphin/"
            "feature_table_adjusted_abundance.tsv",

        diagnostic=
            "results/batch_effect/predictive/mmuphin/"
            "mmuphin_diagnostic.pdf",

        summary=
            "results/batch_effect/predictive/mmuphin/"
            "mmuphin_summary.tsv"

    params:
        batch=
            config[
                "batch_correction"
            ][
                "batch_variable"
            ]

    conda:
        "envs/r_batch.yaml"

    log:
        "logs/batch_effect/"
        "predictive_mmuphin_sensitivity.log"

    shell:
        r"""
        set -euo pipefail

        mkdir -p \
            results/batch_effect/predictive/mmuphin

        mkdir -p \
            $(dirname {log})

        Rscript \
            scripts/R/mmuphin_predictive_correction.R \
            "{input.table}" \
            "{input.metadata}" \
            "{params.batch}" \
            "{output.table}" \
            "{output.diagnostic}" \
            "{output.summary}" \
            > "{log}" 2>&1

        test -s "{output.table}"
        test -s "{output.diagnostic}"
        test -s "{output.summary}"
        """