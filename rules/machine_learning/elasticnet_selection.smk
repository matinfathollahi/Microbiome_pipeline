rule elasticnet_selection:

    input:

        "results/machine_learning/feature_selection/train_variance.tsv"

    output:

        train="results/machine_learning/feature_selection/train_elasticnet.tsv",

        features="results/machine_learning/feature_selection/elasticnet_features.tsv",

        coef="results/machine_learning/feature_selection/elasticnet_coefficients.tsv"

    log:

        "logs/machine_learning/elasticnet.log"

    benchmark:

        "benchmark/machine_learning/elasticnet.txt"

    conda:

        "envs/ml.yaml"

    params:

        cv=config["machine_learning"]["elasticnet"]["cv"],

        l1=config["machine_learning"]["elasticnet"]["l1_ratio"],

        seed=config["machine_learning"]["elasticnet"]["random_seed"],

        label=
            config["machine_learning"]["label"],

        metadata=",".join(
            config["machine_learning"]["metadata_columns"]
        )

    shell:

        """
        python scripts/python/elasticnet_selection.py \
            --input {input} \
            --cv {params.cv} \
            --l1 {params.l1} \
            --seed {params.seed} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output {output.train} \
            --feature_output {output.features} \
            --coef_output {output.coef} \
            > {log} 2>&1
        """