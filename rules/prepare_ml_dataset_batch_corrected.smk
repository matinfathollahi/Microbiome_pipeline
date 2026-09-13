rule prepare_ml_dataset_batch_corrected_sensitivity:
    input:
        table=
            "results/batch_effect/predictive/mmuphin/"
            "feature_table_adjusted_abundance.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:
        dataset=
            "results/machine_learning_batch_corrected/"
            "dataset.tsv"

    params:
        label=
            config[
                "machine_learning"
            ][
                "label"
            ],

        metadata_columns=
            ",".join(
                config[
                    "machine_learning"
                ][
                    "metadata_columns"
                ]
            )

    conda:
        "envs/R.yaml"

    log:
        "logs/machine_learning_batch_corrected/"
        "prepare_dataset.log"

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected

        mkdir -p \
            logs/machine_learning_batch_corrected

        Rscript \
            scripts/R/prepare_ml_dataset.R \
            "{input.table}" \
            "{input.metadata}" \
            "{params.label}" \
            "{params.metadata_columns}" \
            "{output.dataset}" \
            > "{log}" 2>&1
        """