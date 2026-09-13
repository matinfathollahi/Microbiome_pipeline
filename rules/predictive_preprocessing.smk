rule predictive_preprocessing:
    input:
        train=
            "results/machine_learning/train.tsv",

        test=
            "results/machine_learning/test.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:
        train=
            "results/machine_learning/preprocessing/train_clr.tsv",

        test=
            "results/machine_learning/preprocessing/test_clr.tsv",

        features=
            "results/machine_learning/preprocessing/selected_features.tsv",

        preprocessor=
            "results/machine_learning/preprocessing/preprocessor.joblib",

        summary=
            "results/machine_learning/preprocessing/summary.json"

    params:
        min_count=
            config[
                "filtering"
            ][
                "min_count"
            ],

        prevalence=
            config[
                "filtering"
            ][
                "prevalence"
            ],

        zero_fraction=
            config[
                "machine_learning"
            ][
                "predictive_preprocessing"
            ][
                "zero_fraction"
            ]

    log:
        "logs/machine_learning/predictive_preprocessing.log"

    benchmark:
        "benchmark/machine_learning/predictive_preprocessing.txt"

    conda:
        "envs/ml.yaml"

    shell:
        r"""
        mkdir -p results/machine_learning/preprocessing
        mkdir -p $(dirname {log})

        set -euo pipefail

        PYTHONPATH=scripts/python \
        python scripts/python/predictive_preprocessing.py \
            --train {input.train} \
            --test {input.test} \
            --metadata {input.metadata} \
            --min-count {params.min_count} \
            --prevalence {params.prevalence} \
            --zero-fraction {params.zero_fraction} \
            --train-output {output.train} \
            --test-output {output.test} \
            --features-output {output.features} \
            --model-output {output.preprocessor} \
            --summary-output {output.summary} \
            > {log} 2>&1

        test -s {output.train}
        test -s {output.test}
        test -s {output.features}
        test -s {output.preprocessor}
        test -s {output.summary}
        """