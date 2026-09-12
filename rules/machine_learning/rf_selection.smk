rule rf_selection:

    input:

        "results/machine_learning/feature_selection/train_variance.tsv"

    output:

        train="results/machine_learning/feature_selection/train_rf.tsv",

        features="results/machine_learning/feature_selection/rf_features.tsv",

        importance="results/machine_learning/feature_selection/rf_importance.tsv"

    log:

        "logs/machine_learning/rf_selection.log"

    benchmark:

        "benchmark/machine_learning/rf_selection.txt"

    conda:

        "envs/ml.yaml"

    params:

        trees=config["machine_learning"]["random_forest"]["trees"],

        seed=config["machine_learning"]["random_forest"]["random_seed"],

        top=config["machine_learning"]["random_forest"]["top_features"],

        label=
            config["machine_learning"]["label"],

        metadata=",".join(
            config["machine_learning"]["metadata_columns"]
        )

    shell:

        """
        python scripts/python/rf_selection.py \
            --input {input} \
            --trees {params.trees} \
            --seed {params.seed} \
            --top {params.top} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output {output.train} \
            --feature_output {output.features} \
            --importance_output {output.importance} \
            > {log} 2>&1
        """