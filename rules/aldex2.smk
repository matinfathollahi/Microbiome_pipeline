rule aldex2_supplementary:

    input:
        table="results/export/feature_table/feature-table.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        all_results="results/aldex2/all_glm_results.tsv",
        group_results="results/aldex2/group_results.tsv",
        significant="results/aldex2/significant_results.tsv",
        eligibility="results/aldex2/study_eligibility.tsv",
        summary="results/aldex2/analysis_summary.tsv"

    params:
        outdir="results/aldex2",

        sample_column=config["differential_abundance"]["sample_column"],
        study_column=config["differential_abundance"]["study_column"],
        group_column=config["differential_abundance"]["group_column"],

        reference_group=config["differential_abundance"]["reference_group"],
        case_group=config["differential_abundance"]["case_group"],

        min_samples=config["differential_abundance"]["min_samples_per_group"],
        min_studies=config["differential_abundance"]["min_studies"],

        prevalence=config["differential_abundance"]["prevalence"],
        alpha=config["differential_abundance"]["alpha"],

        mc_samples=config.get(
            "supplementary_differential_abundance", {}
        ).get(
            "aldex2", {}
        ).get(
            "mc_samples", 128
        ),

        fdr_method=config.get(
            "supplementary_differential_abundance", {}
        ).get(
            "aldex2", {}
        ).get(
            "fdr_method", "BH"
        )

    log:
        "logs/aldex2/aldex2.log"

    benchmark:
        "benchmark/aldex2/aldex2.txt"

    conda:
        "envs/r_aldex2.yaml"

    shell:
        r"""
        mkdir -p {params.outdir}
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/aldex2.R \
            "{input.table}" \
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
            {params.mc_samples} \
            {params.alpha} \
            "{params.fdr_method}" \
            > "{log}" 2>&1

        test -s "{output.all_results}"
        test -s "{output.group_results}"
        test -f "{output.significant}"
        test -s "{output.eligibility}"
        test -s "{output.summary}"
        """