rule ancombc2:
    input:
        table=
            "results/export/feature_table/feature-table.tsv",

        taxonomy=
            "results/export/taxonomy/taxonomy.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:
        all_results=
            "results/ancombc2/all_results.tsv",

        significant=
            "results/ancombc2/significant_results.tsv",

        eligibility=
            "results/ancombc2/study_eligibility.tsv",

        summary=
            "results/ancombc2/analysis_summary.tsv"

    params:
        outdir=
            "results/ancombc2",

        sample_column=
            config["differential_abundance"]["sample_column"],

        study_column=
            config["differential_abundance"]["study_column"],

        group_column=
            config["differential_abundance"]["group_column"],

        reference_group=
            config["differential_abundance"]["reference_group"],

        case_group=
            config["differential_abundance"]["case_group"],

        min_samples=
            config["differential_abundance"]["min_samples_per_group"],

        min_studies=
            config["differential_abundance"]["min_studies"],

        prevalence=
            config["differential_abundance"]["prevalence"],

        alpha=
            config["differential_abundance"]["alpha"],

        p_adjust=
            config["differential_abundance"]["p_adjust_method"]

    threads:
        config["differential_abundance"]["threads"]

    log:
        "logs/ancombc2/ancombc2.log"

    benchmark:
        "benchmark/ancombc2/ancombc2.txt"

    conda:
        "envs/r_ancombc.yaml"

    shell:
        r"""
        mkdir -p {params.outdir}
        mkdir -p $(dirname {log})

        set -euo pipefail

        Rscript scripts/R/ancombc.R \
            "{input.table}" \
            "{input.taxonomy}" \
            "{input.metadata}" \
            "{params.outdir}" \
            "{params.sample_column}" \
            "{params.study_column}" \
            "{params.group_column}" \
            "{params.reference_group}" \
            "{params.case_group}" \
            {params.min_samples} \
            {params.min_studies} \
            {params.prevalence} \
            {params.alpha} \
            "{params.p_adjust}" \
            {threads} \
            > "{log}" 2>&1

        test -s "{output.all_results}"
        test -s "{output.significant}"
        test -s "{output.eligibility}"
        test -s "{output.summary}"
        """