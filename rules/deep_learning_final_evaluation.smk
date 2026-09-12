rule deep_learning_final_evaluation:

    input:

        train=
            "results/machine_learning/train.tsv",

        test=
            "results/machine_learning/test.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv",

        nested=
            "results/deep_learning/nested_cv/nested_summary.json"

    output:

        metrics=
            "results/deep_learning/final/final_test_metrics.tsv",

        predictions=
            "results/deep_learning/final/final_test_predictions.tsv",

        model=
            "results/deep_learning/final/final_model.pt",

        scaler=
            "results/deep_learning/final/scaler.joblib",
        preprocessor=
            "results/deep_learning/final/microbiome_preprocessor.joblib",

        params=
            "results/deep_learning/final/best_parameters.json",

        summary=
            "results/deep_learning/final/final_summary.json"

    params:

        label=
            config[
                "machine_learning"
            ][
                "label"
            ],

        inner_folds=
            config[
                "deep_learning"
            ][
                "inner_folds"
            ],

        trials=
            config[
                "deep_learning"
            ][
                "final_evaluation"
            ][
                "trials"
            ],

        validation_fraction=
            config[
                "deep_learning"
            ][
                "final_evaluation"
            ][
                "validation_fraction"
            ],

        group = config["deep_learning"]["group_column"],

        max_epochs=
            config[
                "deep_learning"
            ][
                "final_evaluation"
            ][
                "max_epochs"
            ],

        seed=
            config[
                "deep_learning"
            ][
                "random_seed"
            ],

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
            ],

        outdir=
            "results/deep_learning/final"

    log:

        "logs/deep_learning/final_evaluation.log"

    benchmark:

        "benchmark/deep_learning/final_evaluation.txt"

    conda:

        "envs/deep_learning.yaml"

    shell:

        r"""
        mkdir -p {params.outdir}
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        PYTHONPATH=scripts/python \
        python -m deep_learning.final_evaluation \
            --train {input.train} \
            --test {input.test} \
            --metadata {input.metadata} \
            --label "{params.label}" \
            --group "{params.group}" \
            --output {params.outdir} \
            --inner-folds {params.inner_folds} \
            --trials {params.trials} \
            --validation-fraction {params.validation_fraction} \
            --max-epochs {params.max_epochs} \
            --seed {params.seed} \
            --min-count {params.min_count} \
            --prevalence {params.prevalence} \
            --zero-fraction {params.zero_fraction} \
            > {log} 2>&1

        test -s {output.metrics}
        test -s {output.predictions}
        test -s {output.model}
        test -s {output.scaler}
        test -s {output.preprocessor}
        test -s {output.params}
        test -s {output.summary}
        """