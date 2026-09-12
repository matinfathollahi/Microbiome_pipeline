rule prepare_deep_learning_data:

    input:
        train=
            "results/machine_learning/train.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:
        features=
            "results/deep_learning/data/train_features.tsv",

        labels=
            "results/deep_learning/data/train_labels.tsv",

        groups=
            "results/deep_learning/data/train_groups.tsv"


    log:
        "logs/deep_learning/prepare_data.log"

    benchmark:
        "benchmark/deep_learning/prepare_data.txt"

    conda:
        "envs/ml.yaml"

    params:
        label=
            config["machine_learning"]["label"],

        group=
            config["deep_learning"]["group_column"]

    shell:
        """
        mkdir -p results/deep_learning/data
        mkdir -p logs/deep_learning
        mkdir -p benchmark/deep_learning

        python scripts/python/deep_learning/prepare_data.py \
            --input {input.train} \
            --metadata {input.metadata} \
            --label "{params.label}" \
            --group "{params.group}" \
            --features {output.features} \
            --labels {output.labels} \
            --groups {output.groups} \
            > {log} 2>&1
        """


rule deep_learning_nested_cv:

    input:
        features=
            "results/deep_learning/data/train_features.tsv",

        labels=
            "results/deep_learning/data/train_labels.tsv",

        groups=
            "results/deep_learning/data/train_groups.tsv",

    output:
        summary=
            "results/deep_learning/nested_cv/nested_summary.json",

        scores=
            "results/deep_learning/nested_cv/nested_scores.tsv",

        params=
            "results/deep_learning/nested_cv/best_parameters_all_folds.tsv",


        artifacts=
            "results/deep_learning/nested_cv/fold_artifacts.tar.gz"

    log:
        "logs/deep_learning/nested_cv.log"

    benchmark:
        "benchmark/deep_learning/nested_cv.txt"

    conda:
        "envs/deep_learning.yaml"

    params:



        inner=
            config["deep_learning"]["inner_folds"],

        trials=
            config["deep_learning"]["inner_trials"],

        seed=
            config["deep_learning"]["random_seed"],

        min_count=
            config["filtering"]["min_count"],

        prevalence=
            config["filtering"]["prevalence"],

        zero_fraction=
            config[
                "machine_learning"
            ][
                "predictive_preprocessing"
            ][
                "zero_fraction"
            ]





    shell:
        """
        mkdir -p results/deep_learning/nested_cv
        mkdir -p logs/deep_learning
        mkdir -p benchmark/deep_learning

        rm -rf results/deep_learning/nested_cv/fold_*
        rm -f results/deep_learning/nested_cv/fold_artifacts.tar.gz
        rm -f results/deep_learning/nested_cv/fold_artifacts.tar.gz.tmp

        PYTHONPATH=scripts/python \
        python -m deep_learning.nested_cv \
            --input {input.features} \
            --labels {input.labels} \
            --groups {input.groups} \
            --output results/deep_learning/nested_cv \
            --inner_folds {params.inner} \
            --inner_trials {params.trials} \
            --seed {params.seed} \
            --min_count {params.min_count} \
            --prevalence {params.prevalence} \
            --zero_fraction {params.zero_fraction} \
            > {log} 2>&1

        test -s {output.summary}
        test -s {output.scores}
        test -s {output.params}
        test -s {output.artifacts}
        """