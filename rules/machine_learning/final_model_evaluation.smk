rule final_model_evaluation:

    input:

        train=
            "results/machine_learning/preprocessing/train_clr.tsv",

        test=
            "results/machine_learning/preprocessing/test_clr.tsv",
        features=
            "results/machine_learning/feature_selection/consensus_features.tsv",

        best_model=
            "results/machine_learning/optuna/best_model.json"

    output:

        metrics=
            "results/machine_learning/final/final_test_metrics.tsv",

        predictions=
            "results/machine_learning/final/final_test_predictions.tsv",

        params=
            "results/machine_learning/final/final_best_params.json",

        trials=
            "results/machine_learning/final/final_tuning_trials.tsv",

        features=
            "results/machine_learning/final/final_features.tsv",

        classes=
            "results/machine_learning/final/label_classes.json",

        model=
            "results/machine_learning/final/final_model.joblib"

    log:

        "logs/machine_learning/final_model_evaluation.log"

    benchmark:

        "benchmark/machine_learning/final_model_evaluation.txt"

    conda:

        "envs/ml.yaml"

    params:

        label=
            config["machine_learning"]["label"],

        metadata=
            ",".join(
                config[
                    "machine_learning"
                ][
                    "metadata_columns"
                ]
            ),

        cv=
            config[
                "machine_learning"
            ][
                "nested_cv"
            ][
                "inner_folds"
            ],

        trials=
            config[
                "machine_learning"
            ][
                "optuna"
            ][
                "trials"
            ],

        timeout=
            config[
                "machine_learning"
            ][
                "optuna"
            ][
                "timeout"
            ],

        seed=
            config[
                "machine_learning"
            ][
                "optuna"
            ][
                "random_seed"
            ],

        group=
            config[
                "machine_learning"
            ][
                "group_column"
            ],

    shell:
        """
        python scripts/python/final_model_evaluation.py \
            --train {input.train} \
            --test {input.test} \
            --features {input.features} \
            --best_model {input.best_model} \
            --label "{params.label}" \
            --group "{params.group}" \
            --metadata "{params.metadata}" \
            --cv {params.cv} \
            --trials {params.trials} \
            --timeout {params.timeout} \
            --seed {params.seed} \
            --output results/machine_learning/final \
            > {log} 2>&1
        """