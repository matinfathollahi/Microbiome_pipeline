rule maaslin2_supplementary:
    input:
        table="results/export/feature_table/feature-table.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        all_results="results/maaslin2/all_results.tsv",
        group_results="results/maaslin2/group_results.tsv",
        significant="results/maaslin2/group_significant_results.tsv",
        eligibility="results/maaslin2/study_eligibility.tsv",
        summary="results/maaslin2/analysis_summary.tsv"

    params:
        outdir="results/maaslin2",

        sample_column=config["differential_abundance"]["sample_column"],
        study_column=config["differential_abundance"]["study_column"],
        group_column=config["differential_abundance"]["group_column"],

        reference_group=config["differential_abundance"]["reference_group"],
        case_group=config["differential_abundance"]["case_group"],

        min_samples=config["differential_abundance"]["min_samples_per_group"],
        min_studies=config["differential_abundance"]["min_studies"],

        prevalence=config["differential_abundance"]["prevalence"],
        alpha=config["differential_abundance"]["alpha"],

        normalization=config.get(
            "supplementary_differential_abundance", {}
        ).get("maaslin2", {}).get("normalization", "TSS"),

        transform=config.get(
            "supplementary_differential_abundance", {}
        ).get("maaslin2", {}).get("transform", "LOG"),

        analysis_method=config.get(
            "supplementary_differential_abundance", {}
        ).get("maaslin2", {}).get("analysis_method", "LM")

    log:
        "logs/maaslin2/maaslin2.log"

    benchmark:
        "benchmark/maaslin2/maaslin2.txt"

    conda:
        "envs/r_maaslin2.yaml"

    shell:
        r"""
        mkdir -p {params.outdir}
        mkdir -p $(dirname {log})

        set -euo pipefail

        Rscript scripts/R/maaslin2.R \
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
            {params.alpha} \
            "{params.normalization}" \
            "{params.transform}" \
            "{params.analysis_method}" \
            > "{log}" 2>&1

        test -s "{output.all_results}"
        test -s "{output.group_results}"
        test -f "{output.significant}"
        test -s "{output.eligibility}"
        test -s "{output.summary}"
        """