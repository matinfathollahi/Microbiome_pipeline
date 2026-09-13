rule train_test_split:
    input:
        dataset=
            "results/machine_learning/dataset.tsv"

    output:
        train=
            "results/machine_learning/train.tsv",

        test=
            "results/machine_learning/test.tsv",

        train_samples=
            "results/machine_learning/split/"
            "train_samples.tsv",

        test_samples=
            "results/machine_learning/split/"
            "test_samples.tsv"

    log:
        "logs/machine_learning/train_test_split.log"

    benchmark:
        "benchmark/machine_learning/train_test_split.txt"

    conda:
        "envs/ml.yaml"

    params:
        label=
            config[
                "machine_learning"
            ][
                "label"
            ],

        group=
            config[
                "machine_learning"
            ][
                "group_column"
            ],

        frac=
            config[
                "machine_learning"
            ][
                "train_fraction"
            ],

        seed=
            config[
                "machine_learning"
            ][
                "random_seed"
            ],

        stratify_flag=(
            ""
            if config[
                "machine_learning"
            ][
                "stratify"
            ]
            else "--no_stratify"
        )

    shell:
        r"""
        mkdir -p \
            results/machine_learning/split

        mkdir -p \
            logs/machine_learning

        mkdir -p \
            benchmark/machine_learning

        python \
            scripts/python/train_test_split.py \
            --input "{input.dataset}" \
            --label "{params.label}" \
            --group "{params.group}" \
            --train_fraction {params.frac} \
            --seed {params.seed} \
            {params.stratify_flag} \
            --train-samples "{output.train_samples}" \
            --test-samples "{output.test_samples}" \
            --train_output "{output.train}" \
            --test_output "{output.test}" \
            > "{log}" 2>&1

        test -s "{output.train}"
        test -s "{output.test}"
        test -s "{output.train_samples}"
        test -s "{output.test_samples}"
        """