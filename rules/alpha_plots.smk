rule alpha_plots:

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
        directory("results/figures/alpha")

    params:
        alpha_dir="results/export/alpha"

    log:
        "logs/R/alpha_plots.log"

    benchmark:
        "benchmark/R/alpha_plots.txt"

    conda:
        "envs/R.yaml"

    shell:
        """
        bash scripts/bash/run_alpha_plots.sh \
            {params.alpha_dir} \
            {input.metadata} \
            {output} \
            > {log} 2>&1
        """