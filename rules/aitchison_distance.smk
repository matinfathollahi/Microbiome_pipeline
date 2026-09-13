rule aitchison_distance:
    input:
        "results/batch_effect/feature_table_clr.tsv"

    output:
        "results/batch_effect/distance/aitchison_distance.tsv"

    log:
        "logs/batch_effect/aitchison_distance.log"

    benchmark:
        "benchmark/batch_effect/aitchison_distance.txt"

    conda:
        "envs/r_batch.yaml"

    shell:
        """
        mkdir -p results/batch_effect/distance

        Rscript scripts/R/aitchison_distance.R \
            {input} \
            {output} \
            > {log} 2>&1
        """