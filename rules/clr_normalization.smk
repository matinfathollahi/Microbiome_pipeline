rule clr_normalization:

    input:
        "results/selbal/feature_table_zero_replaced.tsv"

    output:
        "results/batch_effect/feature_table_clr.tsv"

    log:
        "logs/batch_effect/clr_normalization.log"

    benchmark:
        "benchmark/batch_effect/clr_normalization.txt"

    conda:
        "envs/r_batch.yaml"

    shell:
        """
        mkdir -p results/batch_effect

        Rscript scripts/R/clr_normalization.R \
            {input} \
            {output} \
            > {log} 2>&1
        """