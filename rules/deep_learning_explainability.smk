rule deep_learning_explainability:

    input:

        features=
            "results/deep_learning/data/train_features.tsv",

        labels=
            "results/deep_learning/data/train_labels.tsv",

        nested_complete=
            "results/deep_learning/nested_cv/nested_summary.json",

        artifacts=
            "results/deep_learning/nested_cv/fold_artifacts.tar.gz"

    output:

        summary=
            "results/deep_learning/explainability/explainability_summary.json",

        consensus=
            "results/deep_learning/explainability/consensus_importance.tsv",

        shap=
            "results/deep_learning/explainability/global_shap_importance.tsv",

        ig=
            "results/deep_learning/explainability/global_ig_importance.tsv",

        permutation=
            "results/deep_learning/explainability/global_permutation_importance.tsv",

        local=
            "results/deep_learning/explainability/local_shap_explanations.tsv"

    params:

        outdir=
            "results/deep_learning/explainability",



        seed=
            config[
                "deep_learning"
            ][
                "random_seed"
            ],

        background_size=
            config[
                "deep_learning"
            ][
                "explainability"
            ][
                "background_size"
            ],

        max_samples=
            config[
                "deep_learning"
            ][
                "explainability"
            ][
                "max_explain_samples"
            ],

        ig_steps=
            config[
                "deep_learning"
            ][
                "explainability"
            ][
                "ig_steps"
            ],

        permutation_repeats=
            config[
                "deep_learning"
            ][
                "explainability"
            ][
                "permutation_repeats"
            ],

        permutation_max_features=
            config[
                "deep_learning"
            ][
                "explainability"
            ][
                "permutation_max_features"
            ],

        top_features=
            config[
                "deep_learning"
            ][
                "explainability"
            ][
                "top_features"
            ]

    log:
        "logs/deep_learning/explainability.log"

    benchmark:
        "benchmark/deep_learning/explainability.txt"

    conda:
        "envs/deep_learning.yaml"

    shell:
        r"""
        mkdir -p {params.outdir}
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        MODELS_DIR="$(mktemp -d)"
        trap 'rm -rf "$MODELS_DIR"' EXIT

        tar -tzf {input.artifacts} > /dev/null

        tar -xzf \
            {input.artifacts} \
            -C "$MODELS_DIR"

        PYTHONPATH=scripts/python \
        python -m deep_learning.explainability.run_explainability \
            --features {input.features} \
            --labels {input.labels} \
            --models-dir "$MODELS_DIR" \
            --output {params.outdir} \
            --seed {params.seed} \
            --background-size {params.background_size} \
            --max-explain-samples {params.max_samples} \
            --ig-steps {params.ig_steps} \
            --permutation-repeats {params.permutation_repeats} \
            --permutation-max-features {params.permutation_max_features} \
            --top-features {params.top_features} \
            > {log} 2>&1

        test -s {output.summary}
        test -s {output.consensus}
        test -s {output.shap}
        test -s {output.ig}
        test -s {output.permutation}
        test -s {output.local}
        """