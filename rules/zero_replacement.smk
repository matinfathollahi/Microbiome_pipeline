rule zero_replacement:
    input:
        "results/filtering/feature_table_filtered.tsv"

    output:
        "results/selbal/feature_table_zero_replaced.tsv"

    log:
        "logs/selbal/zero_replacement.log"

    benchmark:
        "benchmark/selbal/zero_replacement.txt"

    conda:
        "envs/r_selbal.yaml"

    shell:
        """
        mkdir -p results/selbal

        Rscript scripts/R/zero_replacement.R \
            {input} \
            {output} \
            > {log} 2>&1
        """