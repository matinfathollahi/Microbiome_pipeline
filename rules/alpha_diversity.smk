wildcard_constraints:
    metric="faith_pd|shannon|evenness|observed_features"


rule alpha_diversity:

    input:
        core_metrics="results/qiime2/diversity/core_metrics",
        metadata="metadata/sample_metadata.tsv"

    output:
        "results/qiime2/alpha/{metric}_significance.qzv"

    params:
        alpha=lambda wildcards: (
            f"results/qiime2/diversity/core_metrics/"
            f"{wildcards.metric}_vector.qza"
        )

    log:
        "logs/qiime2/alpha_{metric}.log"

    benchmark:
        "benchmark/qiime2/alpha_{metric}.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        bash scripts/bash/alpha_diversity.sh \
            {params.alpha} \
            {input.metadata} \
            {output} \
            > {log} 2>&1
        """