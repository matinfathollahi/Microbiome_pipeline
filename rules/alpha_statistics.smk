rule alpha_statistics:
    input:
        alpha=expand(
            "results/export/alpha/{metric}/alpha-diversity.tsv",
            metric=[
                "faith_pd",
                "shannon",
                "evenness",
                "observed_features"
            ]
        ),
        metadata="metadata/sample_metadata.tsv"

    output:
        directory("results/statistics/alpha")

    params:
        alpha_dir="results/export/alpha",
        study_column=config["alpha_statistics"]["study_column"],
        reference_group=config["alpha_statistics"]["reference_group"],
        case_group=config["alpha_statistics"]["case_group"],
        min_samples=config["alpha_statistics"]["min_samples_per_group"],
        min_studies=config["alpha_statistics"]["min_studies"],
        meta_method=config["alpha_statistics"]["meta_method"]

    log:
        "logs/R/alpha_statistics.log"

    benchmark:
        "benchmark/R/alpha_statistics.txt"

    conda:
        "envs/R.yaml"

    shell:
        """
        Rscript scripts/R/alpha_statistics.R \
            {params.alpha_dir} \
            {input.metadata} \
            {output} \
            "{params.study_column}" \
            "{params.reference_group}" \
            "{params.case_group}" \
            {params.min_samples} \
            {params.min_studies} \
            "{params.meta_method}" \
            > {log} 2>&1
    """