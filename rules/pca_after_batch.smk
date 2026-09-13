rule pca_after_batch:
    input:
        table="results/batch_effect/corrected/feature_table_corrected.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        directory("results/batch_correction/pca")

    log:
        "logs/batch_correction/pca_after.log"

    benchmark:
        "benchmark/batch_correction/pca_after.txt"

    conda:
        "envs/R.yaml"

    shell:
        r"""
        mkdir -p {output}
        mkdir -p $(dirname {log})

        set -euo pipefail

        Rscript scripts/R/pca_after_batch.R \
            {input.table} \
            {input.metadata} \
            {output} \
            > {log} 2>&1
        """