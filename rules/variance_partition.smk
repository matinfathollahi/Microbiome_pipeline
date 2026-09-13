rule variance_partition:
    input:
        table="results/batch_effect/feature_table_clr.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        table="results/batch_effect/variance_partition/variance_partition.tsv",
        figure="results/batch_effect/variance_partition/variance_partition.pdf"

    params:
        variables=",".join(config["variance_partition"]["variables"])

    log:
        "logs/batch_effect/variance_partition.log"

    benchmark:
        "benchmark/batch_effect/variance_partition.txt"

    conda:
        "envs/r_batch.yaml"

    shell:
        """
        mkdir -p results/batch_effect/variance_partition

        Rscript scripts/R/variance_partition.R \
            {input.table} \
            {input.metadata} \
            "{params.variables}" \
            results/batch_effect/variance_partition \
            > {log} 2>&1
        """