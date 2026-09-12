rule boruta_selection:

    input:

        "results/machine_learning/feature_selection/train_variance.tsv"

    output:

        train="results/machine_learning/feature_selection/train_boruta.tsv",

        features="results/machine_learning/feature_selection/boruta_features.tsv",

        ranking="results/machine_learning/feature_selection/boruta_ranking.tsv"

    log:

        "logs/machine_learning/boruta.log"

    benchmark:

        "benchmark/machine_learning/boruta.txt"

    conda:

        "envs/ml.yaml"

    params:

        trees=config["machine_learning"]["boruta"]["n_estimators"],

        iters=config["machine_learning"]["boruta"]["max_iter"],

        seed=config["machine_learning"]["boruta"]["random_seed"],

        label=
            config["machine_learning"]["label"],

        metadata=",".join(
            config["machine_learning"]["metadata_columns"]
        )

    shell:

        """
        python scripts/python/boruta_selection.py \
            --input {input} \
            --trees {params.trees} \
            --max_iter {params.iters} \
            --seed {params.seed} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output {output.train} \
            --feature_output {output.features} \
            --ranking_output {output.ranking} \
            > {log} 2>&1
        """