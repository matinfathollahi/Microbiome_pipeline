rule variance_filter_batch_corrected:

    input:

        "results/machine_learning_batch_corrected/"
        "preprocessing/train_clr.tsv"

    output:

        train=
            "results/machine_learning_batch_corrected/"
            "feature_selection/train_variance.tsv",

        selected=
            "results/machine_learning_batch_corrected/"
            "feature_selection/selected_variance_features.tsv",

        removed=
            "results/machine_learning_batch_corrected/"
            "feature_selection/variance_removed_features.tsv"

    log:

        "logs/machine_learning_batch_corrected/"
        "variance_filter.log"

    benchmark:

        "benchmark/machine_learning_batch_corrected/"
        "variance_filter.txt"

    conda:

        "envs/ml.yaml"

    params:

        threshold=
            config[
                "machine_learning"
            ][
                "variance_filter"
            ][
                "threshold"
            ],

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
            )

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected/feature_selection

        mkdir -p \
            $(dirname {log})

        mkdir -p \
            $(dirname {benchmark})

        python scripts/python/variance_filter.py \
            --input "{input}" \
            --threshold {params.threshold} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output "{output.train}" \
            --selected_output "{output.selected}" \
            --removed_output "{output.removed}" \
            > "{log}" 2>&1

        test -s "{output.train}"
        test -s "{output.selected}"
        test -s "{output.removed}"
        """



rule boruta_selection_batch_corrected:

    input:

        "results/machine_learning_batch_corrected/"
        "feature_selection/train_variance.tsv"

    output:

        train=
            "results/machine_learning_batch_corrected/"
            "feature_selection/train_boruta.tsv",

        features=
            "results/machine_learning_batch_corrected/"
            "feature_selection/boruta_features.tsv",

        ranking=
            "results/machine_learning_batch_corrected/"
            "feature_selection/boruta_ranking.tsv"

    log:

        "logs/machine_learning_batch_corrected/"
        "boruta.log"

    benchmark:

        "benchmark/machine_learning_batch_corrected/"
        "boruta.txt"

    conda:

        "envs/ml.yaml"

    params:

        trees=
            config[
                "machine_learning"
            ][
                "boruta"
            ][
                "n_estimators"
            ],

        iters=
            config[
                "machine_learning"
            ][
                "boruta"
            ][
                "max_iter"
            ],

        seed=
            config[
                "machine_learning"
            ][
                "boruta"
            ][
                "random_seed"
            ],

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
            )

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected/feature_selection

        mkdir -p \
            $(dirname {log})

        mkdir -p \
            $(dirname {benchmark})

        python scripts/python/boruta_selection.py \
            --input "{input}" \
            --trees {params.trees} \
            --max_iter {params.iters} \
            --seed {params.seed} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output "{output.train}" \
            --feature_output "{output.features}" \
            --ranking_output "{output.ranking}" \
            > "{log}" 2>&1

        test -s "{output.train}"
        test -s "{output.features}"
        test -s "{output.ranking}"
        """



rule elasticnet_selection_batch_corrected:

    input:

        "results/machine_learning_batch_corrected/"
        "feature_selection/train_variance.tsv"

    output:

        train=
            "results/machine_learning_batch_corrected/"
            "feature_selection/train_elasticnet.tsv",

        features=
            "results/machine_learning_batch_corrected/"
            "feature_selection/elasticnet_features.tsv",

        coef=
            "results/machine_learning_batch_corrected/"
            "feature_selection/elasticnet_coefficients.tsv"

    log:

        "logs/machine_learning_batch_corrected/"
        "elasticnet.log"

    benchmark:

        "benchmark/machine_learning_batch_corrected/"
        "elasticnet.txt"

    conda:

        "envs/ml.yaml"

    params:

        cv=
            config[
                "machine_learning"
            ][
                "elasticnet"
            ][
                "cv"
            ],

        l1=
            config[
                "machine_learning"
            ][
                "elasticnet"
            ][
                "l1_ratio"
            ],

        seed=
            config[
                "machine_learning"
            ][
                "elasticnet"
            ][
                "random_seed"
            ],

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
            )

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected/feature_selection

        mkdir -p \
            $(dirname {log})

        mkdir -p \
            $(dirname {benchmark})

        python scripts/python/elasticnet_selection.py \
            --input "{input}" \
            --cv {params.cv} \
            --l1 {params.l1} \
            --seed {params.seed} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output "{output.train}" \
            --feature_output "{output.features}" \
            --coef_output "{output.coef}" \
            > "{log}" 2>&1

        test -s "{output.train}"
        test -s "{output.features}"
        test -s "{output.coef}"
        """



rule rf_selection_batch_corrected:

    input:

        "results/machine_learning_batch_corrected/"
        "feature_selection/train_variance.tsv"

    output:

        train=
            "results/machine_learning_batch_corrected/"
            "feature_selection/train_rf.tsv",

        features=
            "results/machine_learning_batch_corrected/"
            "feature_selection/rf_features.tsv",

        importance=
            "results/machine_learning_batch_corrected/"
            "feature_selection/rf_importance.tsv"

    log:

        "logs/machine_learning_batch_corrected/"
        "rf_selection.log"

    benchmark:

        "benchmark/machine_learning_batch_corrected/"
        "rf_selection.txt"

    conda:

        "envs/ml.yaml"

    params:

        trees=
            config[
                "machine_learning"
            ][
                "random_forest"
            ][
                "trees"
            ],

        seed=
            config[
                "machine_learning"
            ][
                "random_forest"
            ][
                "random_seed"
            ],

        top=
            config[
                "machine_learning"
            ][
                "random_forest"
            ][
                "top_features"
            ],

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
            )

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected/feature_selection

        mkdir -p \
            $(dirname {log})

        mkdir -p \
            $(dirname {benchmark})

        python scripts/python/rf_selection.py \
            --input "{input}" \
            --trees {params.trees} \
            --seed {params.seed} \
            --top {params.top} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output "{output.train}" \
            --feature_output "{output.features}" \
            --importance_output "{output.importance}" \
            > "{log}" 2>&1

        test -s "{output.train}"
        test -s "{output.features}"
        test -s "{output.importance}"
        """



rule consensus_selection_batch_corrected:

    input:

        train=
            "results/machine_learning_batch_corrected/"
            "feature_selection/train_variance.tsv",

        boruta=
            "results/machine_learning_batch_corrected/"
            "feature_selection/boruta_features.tsv",

        elastic=
            "results/machine_learning_batch_corrected/"
            "feature_selection/elasticnet_features.tsv",

        rf=
            "results/machine_learning_batch_corrected/"
            "feature_selection/rf_features.tsv"

    output:

        train=
            "results/machine_learning_batch_corrected/"
            "feature_selection/train_consensus.tsv",

        features=
            "results/machine_learning_batch_corrected/"
            "feature_selection/consensus_features.tsv"

    log:

        "logs/machine_learning_batch_corrected/"
        "consensus.log"

    benchmark:

        "benchmark/machine_learning_batch_corrected/"
        "consensus.txt"

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

        minimum=
            config[
                "machine_learning"
            ][
                "consensus"
            ][
                "min_methods"
            ]

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected/feature_selection

        mkdir -p \
            $(dirname {log})

        mkdir -p \
            $(dirname {benchmark})

        python scripts/python/consensus_selection.py \
            --train "{input.train}" \
            --boruta "{input.boruta}" \
            --elastic "{input.elastic}" \
            --rf "{input.rf}" \
            --minimum {params.minimum} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --train_output "{output.train}" \
            --feature_output "{output.features}" \
            > "{log}" 2>&1

        test -s "{output.train}"
        test -s "{output.features}"
        """