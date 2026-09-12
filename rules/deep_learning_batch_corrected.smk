# IMPORTANT:
# This dataset belongs to the MMUPHin-corrected
# transductive sensitivity branch.
#
# Raw DL remains the primary strict inductive analysis.
#
# Upstream MMUPHin harmonization used the complete
# feature distribution before the fixed train/test split.

rule prepare_deep_learning_data_batch_corrected:

    input:

        train=
            "results/machine_learning_batch_corrected/train.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:

        features=
            "results/deep_learning/batch_corrected/"
            "data/train_features.tsv",

        labels=
            "results/deep_learning/batch_corrected/"
            "data/train_labels.tsv",

        groups=
            "results/deep_learning/batch_corrected/"
            "data/train_groups.tsv"

    log:

        "logs/deep_learning/batch_corrected/"
        "prepare_data.log"

    benchmark:

        "benchmark/deep_learning/batch_corrected/"
        "prepare_data.txt"

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
                "deep_learning"
            ][
                "group_column"
            ]

    shell:

        r"""
        mkdir -p \
            results/deep_learning/batch_corrected/data

        mkdir -p \
            logs/deep_learning/batch_corrected

        mkdir -p \
            benchmark/deep_learning/batch_corrected

        set -euo pipefail

        python \
            scripts/python/deep_learning/prepare_data.py \
            --input "{input.train}" \
            --metadata "{input.metadata}" \
            --label "{params.label}" \
            --group "{params.group}" \
            --features "{output.features}" \
            --labels "{output.labels}" \
            --groups "{output.groups}" \
            > "{log}" 2>&1

        test -s "{output.features}"
        test -s "{output.labels}"
        test -s "{output.groups}"
        """



rule deep_learning_nested_cv_batch_corrected:

    input:

        features=
            "results/deep_learning/batch_corrected/"
            "data/train_features.tsv",

        labels=
            "results/deep_learning/batch_corrected/"
            "data/train_labels.tsv",

        groups=
            "results/deep_learning/batch_corrected/"
            "data/train_groups.tsv"

    output:

        summary=
            "results/deep_learning/batch_corrected/"
            "nested_cv/nested_summary.json",

        scores=
            "results/deep_learning/batch_corrected/"
            "nested_cv/nested_scores.tsv",

        params=
            "results/deep_learning/batch_corrected/"
            "nested_cv/best_parameters_all_folds.tsv",

        artifacts=
            "results/deep_learning/batch_corrected/"
            "nested_cv/fold_artifacts.tar.gz"

    log:

        "logs/deep_learning/batch_corrected/"
        "nested_cv.log"

    benchmark:

        "benchmark/deep_learning/batch_corrected/"
        "nested_cv.txt"

    conda:

        "envs/deep_learning.yaml"

    params:

        inner=
            config[
                "deep_learning"
            ][
                "inner_folds"
            ],

        trials=
            config[
                "deep_learning"
            ][
                "inner_trials"
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
        analysis_mode=
            config[
                "batch_correction"
            ][
                "predictive_sensitivity"
            ][
                "role"
            ],

    shell:
        r"""
        mkdir -p \
            results/deep_learning/batch_corrected/nested_cv

        mkdir -p \
            logs/deep_learning/batch_corrected

        mkdir -p \
            benchmark/deep_learning/batch_corrected

        rm -rf \
            results/deep_learning/batch_corrected/nested_cv/fold_*

        rm -f \
            results/deep_learning/batch_corrected/nested_cv/fold_artifacts.tar.gz

        rm -f \
            results/deep_learning/batch_corrected/nested_cv/fold_artifacts.tar.gz.tmp

        set -euo pipefail

        PYTHONPATH=scripts/python \
        python -m deep_learning.nested_cv \
            --input "{input.features}" \
            --labels "{input.labels}" \
            --groups "{input.groups}" \
            --output \
                results/deep_learning/batch_corrected/nested_cv \
            --inner_folds {params.inner} \
            --inner_trials {params.trials} \
            --seed {params.seed} \
            --min_count {params.min_count} \
            --prevalence {params.prevalence} \
            --zero_fraction {params.zero_fraction} \
            --analysis-mode "{params.analysis_mode}" \
            > "{log}" 2>&1

        test -s "{output.summary}"
        test -s "{output.scores}"
        test -s "{output.params}"
        test -s "{output.artifacts}"
        """


rule deep_learning_final_evaluation_batch_corrected:

    input:

        train=
            "results/machine_learning_batch_corrected/train.tsv",

        test=
            "results/machine_learning_batch_corrected/test.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv",

        nested=
            "results/deep_learning/batch_corrected/"
            "nested_cv/nested_summary.json"

    output:

        metrics=
            "results/deep_learning/batch_corrected/"
            "final/final_test_metrics.tsv",

        predictions=
            "results/deep_learning/batch_corrected/"
            "final/final_test_predictions.tsv",

        model=
            "results/deep_learning/batch_corrected/"
            "final/final_model.pt",

        scaler=
            "results/deep_learning/batch_corrected/"
            "final/scaler.joblib",

        preprocessor=
            "results/deep_learning/batch_corrected/"
            "final/microbiome_preprocessor.joblib",

        params=
            "results/deep_learning/batch_corrected/"
            "final/best_parameters.json",

        summary=
            "results/deep_learning/batch_corrected/"
            "final/final_summary.json"

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

        group=
            config[
                "deep_learning"
            ][
                "group_column"
            ],

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

        analysis_mode=
            config[
                "batch_correction"
            ][
                "predictive_sensitivity"
            ][
                "role"
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
            "results/deep_learning/batch_corrected/final"

    log:

        "logs/deep_learning/batch_corrected/"
        "final_evaluation.log"

    benchmark:

        "benchmark/deep_learning/batch_corrected/"
        "final_evaluation.txt"

    conda:

        "envs/deep_learning.yaml"

    shell:

        r"""
        mkdir -p {params.outdir}

        mkdir -p \
            $(dirname {log})

        mkdir -p \
            $(dirname {benchmark})

        set -euo pipefail

        PYTHONPATH=scripts/python \
        python -m deep_learning.final_evaluation \
            --train "{input.train}" \
            --test "{input.test}" \
            --metadata "{input.metadata}" \
            --label "{params.label}" \
            --group "{params.group}" \
            --output "{params.outdir}" \
            --inner-folds {params.inner_folds} \
            --trials {params.trials} \
            --validation-fraction {params.validation_fraction} \
            --max-epochs {params.max_epochs} \
            --seed {params.seed} \
            --min-count {params.min_count} \
            --prevalence {params.prevalence} \
            --zero-fraction {params.zero_fraction} \
            --analysis-mode "{params.analysis_mode}" \
            > "{log}" 2>&1

        test -s "{output.metrics}"
        test -s "{output.predictions}"
        test -s "{output.model}"
        test -s "{output.scaler}"
        test -s "{output.preprocessor}"
        test -s "{output.params}"
        test -s "{output.summary}"
        """




# Visualization of the transductive MMUPHin
# sensitivity DL branch.
# These plots are supplementary and not
# primary inductive predictive evidence.

rule deep_learning_visualization_batch_corrected:

    input:

        features=
            "results/deep_learning/batch_corrected/"
            "data/train_features.tsv",

        labels=
            "results/deep_learning/batch_corrected/"
            "data/train_labels.tsv",

        nested=
            "results/deep_learning/batch_corrected/"
            "nested_cv/nested_summary.json",

        artifacts=
            "results/deep_learning/batch_corrected/"
            "nested_cv/fold_artifacts.tar.gz"

    output:

        summary=
            "results/deep_learning/batch_corrected/"
            "visualization/visualization_summary.json",

        status=
            "results/deep_learning/batch_corrected/"
            "visualization/visualization_status.tsv"

    params:

        outdir=
            "results/deep_learning/batch_corrected/"
            "visualization",

        seed=
            config[
                "deep_learning"
            ][
                "random_seed"
            ],

        perplexity=
            config[
                "deep_learning"
            ][
                "visualization"
            ][
                "tsne_perplexity"
            ],

        iterations=
            config[
                "deep_learning"
            ][
                "visualization"
            ][
                "tsne_iterations"
            ],

        neighbors=
            config[
                "deep_learning"
            ][
                "visualization"
            ][
                "umap_neighbors"
            ],

        min_dist=
            config[
                "deep_learning"
            ][
                "visualization"
            ][
                "umap_min_dist"
            ]

    log:

        "logs/deep_learning/batch_corrected/"
        "visualization.log"

    benchmark:

        "benchmark/deep_learning/batch_corrected/"
        "visualization.txt"

    conda:

        "envs/deep_learning.yaml"

    shell:
        r"""
        mkdir -p "{params.outdir}"
        mkdir -p "$(dirname "{log}")"
        mkdir -p "$(dirname "{benchmark}")"

        set -euo pipefail

        MODELS_DIR="$(mktemp -d)"

        trap 'rm -rf "$MODELS_DIR"' EXIT

        tar -tzf "{input.artifacts}" > /dev/null

        tar -xzf \
            "{input.artifacts}" \
            -C "$MODELS_DIR"

        PYTHONPATH=scripts/python \
        python -m \
            deep_learning.visualization.run_visualization \
            --features "{input.features}" \
            --labels "{input.labels}" \
            --models-dir "$MODELS_DIR" \
            --output "{params.outdir}" \
            --seed {params.seed} \
            --tsne-perplexity {params.perplexity} \
            --tsne-iterations {params.iterations} \
            --umap-neighbors {params.neighbors} \
            --umap-min-dist {params.min_dist} \
            > "{log}" 2>&1

        test -s "{output.summary}"
        test -s "{output.status}"
        """




# Explainability for the transductive MMUPHin
# sensitivity branch.
#
# Feature importance from this branch should be
# interpreted as sensitivity/supporting evidence,
# not as the primary inductive explanation.

rule deep_learning_explainability_batch_corrected:

    input:

        features=
            "results/deep_learning/batch_corrected/"
            "data/train_features.tsv",

        labels=
            "results/deep_learning/batch_corrected/"
            "data/train_labels.tsv",

        nested_complete=
            "results/deep_learning/batch_corrected/"
            "nested_cv/nested_summary.json",

        artifacts=
            "results/deep_learning/batch_corrected/"
            "nested_cv/fold_artifacts.tar.gz"

    output:

        summary=
            "results/deep_learning/batch_corrected/"
            "explainability/explainability_summary.json",

        consensus=
            "results/deep_learning/batch_corrected/"
            "explainability/consensus_importance.tsv",

        shap=
            "results/deep_learning/batch_corrected/"
            "explainability/global_shap_importance.tsv",

        ig=
            "results/deep_learning/batch_corrected/"
            "explainability/global_ig_importance.tsv",

        permutation=
            "results/deep_learning/batch_corrected/"
            "explainability/global_permutation_importance.tsv",

        local=
            "results/deep_learning/batch_corrected/"
            "explainability/local_shap_explanations.tsv"

    params:

        outdir=
            "results/deep_learning/batch_corrected/"
            "explainability",

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

        "logs/deep_learning/batch_corrected/"
        "explainability.log"

    benchmark:

        "benchmark/deep_learning/batch_corrected/"
        "explainability.txt"

    conda:

        "envs/deep_learning.yaml"

    shell:
        r"""
        mkdir -p "{params.outdir}"
        mkdir -p "$(dirname "{log}")"
        mkdir -p "$(dirname "{benchmark}")"

        set -euo pipefail

        MODELS_DIR="$(mktemp -d)"

        trap 'rm -rf "$MODELS_DIR"' EXIT

        tar -tzf \
            "{input.artifacts}" \
            > /dev/null

        tar -xzf \
            "{input.artifacts}" \
            -C "$MODELS_DIR"

        PYTHONPATH=scripts/python \
        python -m \
            deep_learning.explainability.run_explainability \
            --features "{input.features}" \
            --labels "{input.labels}" \
            --models-dir "$MODELS_DIR" \
            --output "{params.outdir}" \
            --seed {params.seed} \
            --background-size {params.background_size} \
            --max-explain-samples {params.max_samples} \
            --ig-steps {params.ig_steps} \
            --permutation-repeats {params.permutation_repeats} \
            --permutation-max-features \
                {params.permutation_max_features} \
            --top-features {params.top_features} \
            > "{log}" 2>&1

        test -s "{output.summary}"
        test -s "{output.consensus}"
        test -s "{output.shap}"
        test -s "{output.ig}"
        test -s "{output.permutation}"
        test -s "{output.local}"
        """