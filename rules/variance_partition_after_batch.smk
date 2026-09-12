rule variance_partition_after_batch:

    input:
        table="results/batch_correction/corrected/feature_table_corrected.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        directory("results/batch_correction/variance_partition")

    log:
        "logs/batch_correction/variance_partition.log"

    benchmark:
        "benchmark/batch_correction/variance_partition.txt"

    conda:
        "envs/r_batch.yaml"

    params:
        variables=",".join(config["variance_partition"]["variables"])

    shell:
        r"""
        mkdir -p {output}
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/variance_partition_after_batch.R \
            {input.table} \
            {input.metadata} \
            "{params.variables}" \
            {output} \
            > {log} 2>&1
        """