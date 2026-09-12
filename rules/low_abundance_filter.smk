rule low_abundance_filter:

    input:
        "results/export/feature_table/feature-table.tsv"

    output:
        "results/filtering/feature_table_abundance.tsv"

    log:
        "logs/filtering/low_abundance.log"

    benchmark:
        "benchmark/filtering/low_abundance.txt"

    conda:
        "envs/r_filtering.yaml"

    params:
        min_count=config["filtering"]["min_count"]
        

    shell:
        """
        mkdir -p results/filtering

        Rscript scripts/R/low_abundance_filter.R \
            {input} \
            {output} \
            {params.min_count} \
            > {log} 2>&1
        """