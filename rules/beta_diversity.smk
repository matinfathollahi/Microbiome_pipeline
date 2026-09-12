rule beta_permanova:

    input:
        core_metrics="results/qiime2/diversity/core_metrics",
        metadata="metadata/sample_metadata.tsv"

    output:
        "results/qiime2/beta/{metric}_permanova.qzv"

    params:
        distance=lambda wildcards: (
            f"results/qiime2/diversity/core_metrics/"
            f"{wildcards.metric}_distance_matrix.qza"
        ),
        column=config["beta"]["metadata_column"],
        permutations=config["beta"]["permutations"],
        pairwise=lambda wildcards: str(
            config["beta"]["pairwise"]
        ).lower()

    wildcard_constraints:
        metric="bray_curtis|jaccard|weighted_unifrac|unweighted_unifrac"

    log:
        "logs/qiime2/beta_permanova_{metric}.log"

    benchmark:
        "benchmark/qiime2/beta_permanova_{metric}.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        bash scripts/bash/beta_permanova.sh \
            {params.distance} \
            {input.metadata} \
            {output} \
            "{params.column}" \
            {params.permutations} \
            {params.pairwise} \
            > {log} 2>&1
        """