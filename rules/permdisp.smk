rule permdisp:

    input:
        core_metrics="results/qiime2/diversity/core_metrics",
        metadata="metadata/sample_metadata.tsv"

    output:
        "results/qiime2/beta/{metric}_permdisp.qzv"

    params:
        distance=lambda wildcards: (
            f"results/qiime2/diversity/core_metrics/"
            f"{wildcards.metric}_distance_matrix.qza"
        ),
        column=config["permdisp"]["metadata_column"],
        permutations=config["permdisp"]["permutations"],
        pairwise=lambda wildcards: str(
            config["permdisp"]["pairwise"]
        ).lower()

    wildcard_constraints:
        metric="bray_curtis|jaccard|weighted_unifrac|unweighted_unifrac"

    log:
        "logs/qiime2/permdisp_{metric}.log"

    benchmark:
        "benchmark/qiime2/permdisp_{metric}.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        bash scripts/bash/permdisp.sh \
            {params.distance} \
            {input.metadata} \
            {output} \
            "{params.column}" \
            {params.permutations} \
            {params.pairwise} \
            > {log} 2>&1
        """