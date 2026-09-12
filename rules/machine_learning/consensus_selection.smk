rule consensus_selection:

    input:

        train="results/machine_learning/feature_selection/train_variance.tsv",

        boruta="results/machine_learning/feature_selection/boruta_features.tsv",

        elastic="results/machine_learning/feature_selection/elasticnet_features.tsv",

        rf="results/machine_learning/feature_selection/rf_features.tsv"

    output:

        train="results/machine_learning/feature_selection/train_consensus.tsv",

        features="results/machine_learning/feature_selection/consensus_features.tsv"

    log:

        "logs/machine_learning/consensus.log"

    benchmark:

        "benchmark/machine_learning/consensus.txt"

    conda:

        "envs/ml.yaml"

    params:

        label=
            config["machine_learning"]["label"],

        metadata=",".join(
            config["machine_learning"]["metadata_columns"]
        ),

        minimum=config["machine_learning"]["consensus"]["min_methods"]

    shell:

        """
        python scripts/python/consensus_selection.py \
            --train {input.train} \
            --boruta {input.boruta} \
            --elastic {input.elastic} \
            --rf {input.rf} \
            --minimum {params.minimum} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output {output.train} \
            --feature_output {output.features} \
            > {log} 2>&1
        """