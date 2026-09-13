rule random_forest:
    input:
        table="results/export/feature_table/feature-table.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        directory("results/random_forest")

    log:
        "logs/random_forest/random_forest.log"

    benchmark:
        "benchmark/random_forest/random_forest.txt"

    conda:
        "envs/r_randomforest.yaml"

    shell:
        """
        mkdir -p {output}

        Rscript scripts/R/random_forest.R \
            {input.table} \
            {input.metadata} \
            {output} \
            > {log} 2>&1
        """