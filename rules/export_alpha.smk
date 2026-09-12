ALPHA_METRICS = [
    "faith_pd",
    "shannon",
    "evenness",
    "observed_features"
]


rule export_alpha:

    input:
        core_metrics="results/qiime2/diversity/core_metrics"

    output:
        "results/export/alpha/{metric}/alpha-diversity.tsv"

    params:
        alpha=lambda wildcards: (
            f"results/qiime2/diversity/core_metrics/"
            f"{wildcards.metric}_vector.qza"
        ),
        outdir=lambda wildcards: (
            f"results/export/alpha/{wildcards.metric}"
        )

    wildcard_constraints:
        metric="faith_pd|shannon|evenness|observed_features"

    log:
        "logs/export/alpha_{metric}.log"

    benchmark:
        "benchmark/export/alpha_{metric}.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        bash scripts/bash/export_alpha.sh \
            {params.alpha} \
            {params.outdir} \
            > {log} 2>&1
        """