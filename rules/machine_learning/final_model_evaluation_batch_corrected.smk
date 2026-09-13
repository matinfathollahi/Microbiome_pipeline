rule final_model_evaluation_batch_corrected:
    input:
        train=
            "results/machine_learning_batch_corrected/"
            "preprocessing/train_clr.tsv",

        test=
            "results/machine_learning_batch_corrected/"
            "preprocessing/test_clr.tsv",

        features=
            "results/machine_learning_batch_corrected/"
            "feature_selection/consensus_features.tsv",

        best_model=
            "results/machine_learning_batch_corrected/"
            "optuna/best_model.json"

    output:
        metrics=
            "results/machine_learning_batch_corrected/"
            "final/final_test_metrics.tsv",

        predictions=
            "results/machine_learning_batch_corrected/"
            "final/final_test_predictions.tsv",

        params=
            "results/machine_learning_batch_corrected/"
            "final/final_best_params.json",

        trials=
            "results/machine_learning_batch_corrected/"
            "final/final_tuning_trials.tsv",

        features=
            "results/machine_learning_batch_corrected/"
            "final/final_features.tsv",

        classes=
            "results/machine_learning_batch_corrected/"
            "final/label_classes.json",

        model=
            "results/machine_learning_batch_corrected/"
            "final/final_model.joblib"

    log:
        "logs/machine_learning_batch_corrected/"
        "final_model_evaluation.log"

    benchmark:
        "benchmark/machine_learning_batch_corrected/"
        "final_model_evaluation.txt"

    conda:
        "envs/ml.yaml"

    params:
        label=
            config[
                "machine_learning"
            ][
                "label"
            ],

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
            ]

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected/final

        mkdir -p \
            $(dirname {log})


        set -euo pipefail

        python scripts/python/final_model_evaluation.py \
            --train "{input.train}" \
            --test "{input.test}" \
            --features "{input.features}" \
            --best_model "{input.best_model}" \
            --label "{params.label}" \
            --group "{params.group}" \
            --metadata "{params.metadata}" \
            --cv {params.cv} \
            --trials {params.trials} \
            --timeout {params.timeout} \
            --seed {params.seed} \
            --output \
                results/machine_learning_batch_corrected/final \
            > "{log}" 2>&1

        test -s "{output.metrics}"
        test -s "{output.predictions}"
        test -s "{output.params}"
        test -s "{output.trials}"
        test -s "{output.features}"
        test -s "{output.classes}"
        test -s "{output.model}"
        """