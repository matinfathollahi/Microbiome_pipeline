rule prepare_ml_dataset:

    input:
        table="results/export/feature_table/feature-table.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        "results/machine_learning/dataset.tsv"

    log:
        "logs/machine_learning/prepare_dataset.log"

    benchmark:
        "benchmark/machine_learning/prepare_dataset.txt"

    conda:
        "envs/R.yaml"

    params:
        label=config["machine_learning"]["label"],

        metadata_columns=",".join(
            config["machine_learning"]["metadata_columns"]
        )

    shell:
        r"""
        mkdir -p $(dirname {output})
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/prepare_ml_dataset.R \
            {input.table} \
            {input.metadata} \
            "{params.label}" \
            "{params.metadata_columns}" \
            {output} \
            > {log} 2>&1
        """