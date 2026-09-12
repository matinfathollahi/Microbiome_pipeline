rule predictive_preprocessing_batch_corrected:

    input:

        train=
            "results/machine_learning_batch_corrected/train.tsv",

        test=
            "results/machine_learning_batch_corrected/test.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:

        train=
            "results/machine_learning_batch_corrected/"
            "preprocessing/train_clr.tsv",

        test=
            "results/machine_learning_batch_corrected/"
            "preprocessing/test_clr.tsv",

        features=
            "results/machine_learning_batch_corrected/"
            "preprocessing/selected_features.tsv",

        preprocessor=
            "results/machine_learning_batch_corrected/"
            "preprocessing/preprocessor.joblib",

        summary=
            "results/machine_learning_batch_corrected/"
            "preprocessing/summary.json"

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

        "logs/machine_learning_batch_corrected/"
        "predictive_preprocessing.log"

    benchmark:

        "benchmark/machine_learning_batch_corrected/"
        "predictive_preprocessing.txt"

    conda:

        "envs/ml.yaml"

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected/preprocessing

        mkdir -p \
            $(dirname {log})

        mkdir -p \
            $(dirname {benchmark})

        set -euo pipefail

        PYTHONPATH=scripts/python \
        python scripts/python/predictive_preprocessing.py \
            --train "{input.train}" \
            --test "{input.test}" \
            --metadata "{input.metadata}" \
            --min-count {params.min_count} \
            --prevalence {params.prevalence} \
            --zero-fraction {params.zero_fraction} \
            --train-output "{output.train}" \
            --test-output "{output.test}" \
            --features-output "{output.features}" \
            --model-output "{output.preprocessor}" \
            --summary-output "{output.summary}" \
            > "{log}" 2>&1

        test -s "{output.train}"
        test -s "{output.test}"
        test -s "{output.features}"
        test -s "{output.preprocessor}"
        test -s "{output.summary}"
        """