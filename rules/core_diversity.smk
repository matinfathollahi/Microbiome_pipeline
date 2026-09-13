rule core_diversity:
    input:
        table="results/qiime2/dada2/feature_table.qza",
        tree="results/qiime2/phylogeny/rooted_tree.qza",
        metadata=f"{config['metadata']}/sample_metadata.tsv"

    output:
        directory("results/qiime2/diversity/core_metrics")

    params:
        sampling_depth=config["diversity"]["sampling_depth"]

    log:
        "logs/qiime2/core_diversity.log"

    benchmark:
        "benchmark/qiime2/core_diversity.txt"

    conda:
        "envs/qiime2.yaml"

    threads:
        config["diversity"]["threads"]

    shell:
        r"""
        mkdir -p {output}
        mkdir -p $(dirname {log})

        set -euo pipefail

        bash scripts/bash/core_diversity.sh \
            {input.table} \
            {input.tree} \
            {input.metadata} \
            {output} \
            {params.sampling_depth} \
            > {log} 2>&1
        """