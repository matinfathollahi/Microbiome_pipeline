rule variance_filter:

    input:

        "results/machine_learning/preprocessing/train_clr.tsv"

    output:

        train="results/machine_learning/feature_selection/train_variance.tsv",

        selected="results/machine_learning/feature_selection/selected_variance_features.tsv",

        removed="results/machine_learning/feature_selection/variance_removed_features.tsv"

    log:

        "logs/machine_learning/variance_filter.log"

    benchmark:

        "benchmark/machine_learning/variance_filter.txt"

    conda:

        "envs/ml.yaml"

    params:

        threshold=config["machine_learning"]["variance_filter"]["threshold"],

        label=
            config["machine_learning"]["label"],

        metadata=",".join(
            config["machine_learning"]["metadata_columns"]
        )

    shell:

        """
        mkdir -p results/machine_learning/feature_selection

        python scripts/python/variance_filter.py \
            --input {input} \
            --threshold {params.threshold} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output {output.train} \
            --selected_output {output.selected} \
            --removed_output {output.removed} \
            > {log} 2>&1
        """