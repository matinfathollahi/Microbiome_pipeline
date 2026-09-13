rule hyperparameter_optimization_batch_corrected:
    input:
        "results/machine_learning_batch_corrected/nested_cv"

    output:
        best_model=
            "results/machine_learning_batch_corrected/"
            "optuna/best_model.json",

        model_summary=
            "results/machine_learning_batch_corrected/"
            "optuna/model_summary.tsv",

        outer_results=
            "results/machine_learning_batch_corrected/"
            "optuna/outer_fold_results.tsv"

    log:
        "logs/machine_learning_batch_corrected/optuna.log"

    benchmark:
        "benchmark/machine_learning_batch_corrected/optuna.txt"

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
            ]

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected/optuna

        mkdir -p \
            $(dirname {log})


        set -euo pipefail

        python scripts/python/optuna_search.py \
            --nested "{input}" \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --trials {params.trials} \
            --timeout {params.timeout} \
            --seed {params.seed} \
            --output \
                results/machine_learning_batch_corrected/optuna \
            > "{log}" 2>&1

        test -s "{output.best_model}"
        test -s "{output.model_summary}"
        test -s "{output.outer_results}"
        """