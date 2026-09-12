rule low_prevalence_filter:

    input:
        "results/filtering/feature_table_abundance.tsv"

    output:
        "results/filtering/feature_table_filtered.tsv"

    log:
        "logs/filtering/low_prevalence.log"

    benchmark:
        "benchmark/filtering/low_prevalence.txt"

    conda:
        "envs/r_filtering.yaml"

    params:
        prevalence=config["filtering"]["prevalence"]
        

    shell:
        """
        Rscript scripts/R/low_prevalence_filter.R \
            {input} \
            {output} \
            {params.prevalence} \
            > {log} 2>&1
        """