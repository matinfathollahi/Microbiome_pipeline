rule batch_before_after_diagnostics:
    input:
        before=
            "results/batch_effect/feature_table_clr.tsv",

        after=
            "results/batch_effect/corrected/feature_table_corrected.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:
        summary=
            "results/batch_effect/diagnostics/summary/batch_diagnostics_summary.tsv",

        comparison=
            "results/batch_effect/diagnostics/summary/batch_diagnostics_comparison.pdf",

        report=
            "results/batch_effect/diagnostics/summary/batch_diagnostics_report.txt",

        pca_before=
            "results/batch_effect/diagnostics/before/pca/pca.pdf",

        pca_after=
            "results/batch_effect/diagnostics/after/pca/pca.pdf",

        pcoa_before=
            "results/batch_effect/diagnostics/before/pcoa/pcoa.pdf",

        pcoa_after=
            "results/batch_effect/diagnostics/after/pcoa/pcoa.pdf",

        permanova_before=
            "results/batch_effect/diagnostics/before/permanova/permanova.tsv",

        permanova_after=
            "results/batch_effect/diagnostics/after/permanova/permanova.tsv",

        variance_before=
            "results/batch_effect/diagnostics/before/variance_partition/variance_partition.tsv",

        variance_after=
            "results/batch_effect/diagnostics/after/variance_partition/variance_partition.tsv"

    params:
        batch=
            config[
                "batch_correction"
            ][
                "batch_variable"
            ],

        group=
            config[
                "batch_correction"
            ][
                "biological_variable"
            ],

        variables=
            ",".join(
                config[
                    "variance_partition"
                ][
                    "variables"
                ]
            ),

        permutations=
            config[
                "permanova"
            ][
                "permutations"
            ],

        outdir=
            "results/batch_effect/diagnostics"

    log:
        "logs/batch_effect/before_after_diagnostics.log"

    benchmark:
        "benchmark/batch_effect/before_after_diagnostics.txt"

    conda:
        "envs/r_batch.yaml"

    shell:
        r"""
        mkdir -p {params.outdir}
        mkdir -p $(dirname {log})

        set -euo pipefail

        Rscript scripts/R/batch_before_after_diagnostics.R \
            {input.before} \
            {input.after} \
            {input.metadata} \
            "{params.batch}" \
            "{params.group}" \
            "{params.variables}" \
            {params.permutations} \
            {params.outdir} \
            > {log} 2>&1

        test -s {output.summary}
        test -s {output.comparison}
        test -s {output.report}

        test -s {output.pca_before}
        test -s {output.pca_after}

        test -s {output.pcoa_before}
        test -s {output.pcoa_after}

        test -s {output.permanova_before}
        test -s {output.permanova_after}

        test -s {output.variance_before}
        test -s {output.variance_after}
        """