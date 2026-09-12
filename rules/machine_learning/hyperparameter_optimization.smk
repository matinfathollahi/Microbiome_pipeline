rule hyperparameter_optimization:

    input:
        "results/machine_learning/nested_cv"

    output:
        best_model=
            "results/machine_learning/optuna/best_model.json",

        model_summary=
            "results/machine_learning/optuna/model_summary.tsv",

        outer_results=
            "results/machine_learning/optuna/outer_fold_results.tsv"

    log:
        "logs/machine_learning/optuna.log"

    benchmark:
        "benchmark/machine_learning/optuna.txt"

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
        """
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        python scripts/python/optuna_search.py \
            --nested {input} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --trials {params.trials} \
            --timeout {params.timeout} \
            --seed {params.seed} \
            --output results/machine_learning/optuna \
            > {log} 2>&1
        """