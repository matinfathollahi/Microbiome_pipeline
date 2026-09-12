rule distance_matrix:

    input:
        table="results/batch_effect/feature_table_clr.tsv",
        tree="results/qiime2/phylogeny/rooted_tree.qza"

    output:
        bray="results/batch_effect/distance/bray_distance.tsv",
        jaccard="results/batch_effect/distance/jaccard_distance.tsv",
        aitchison="results/batch_effect/distance/aitchison_distance.tsv",
        weighted="results/batch_effect/distance/weighted_unifrac_distance.tsv",
        unweighted="results/batch_effect/distance/unweighted_unifrac_distance.tsv"

    log:
        "logs/batch_effect/distance_matrix.log"

    benchmark:
        "benchmark/batch_effect/distance_matrix.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        mkdir -p results/batch_effect/distance

        bash scripts/bash/distance_matrix.sh \
            {input.table} \
            {input.tree} \
            results/batch_effect/distance \
            > {log} 2>&1
        """