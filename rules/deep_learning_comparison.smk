
# IMPORTANT:
# This comparison is:
#
# Raw strict inductive DL
#        versus
# MMUPHin transductive sensitivity DL
#
# Corrected results are supplementary sensitivity
# results, not a second primary inductive pipeline.


rule compare_raw_vs_batch_corrected_dl:

    input:

        raw_metrics=
            "results/deep_learning/final/"
            "final_test_metrics.tsv",

        corrected_metrics=
            "results/deep_learning/batch_corrected/"
            "final/final_test_metrics.tsv",

        raw_predictions=
            "results/deep_learning/final/"
            "final_test_predictions.tsv",

        corrected_predictions=
            "results/deep_learning/batch_corrected/"
            "final/final_test_predictions.tsv",

        raw_nested=
            "results/deep_learning/nested_cv/"
            "nested_scores.tsv",

        corrected_nested=
            "results/deep_learning/batch_corrected/"
            "nested_cv/nested_scores.tsv",

        raw_importance=
            "results/deep_learning/explainability/"
            "consensus_importance.tsv",

        corrected_importance=
            "results/deep_learning/batch_corrected/"
            "explainability/consensus_importance.tsv"

    output:

        metrics=
            "results/deep_learning/comparison/"
            "final_metrics_comparison.tsv",

        predictions=
            "results/deep_learning/comparison/"
            "prediction_comparison.tsv",

        agreement=
            "results/deep_learning/comparison/"
            "prediction_agreement_summary.tsv",

        nested=
            "results/deep_learning/comparison/"
            "nested_cv_comparison.tsv",

        features=
            "results/deep_learning/comparison/"
            "explainability_feature_comparison.tsv",

        overlap=
            "results/deep_learning/comparison/"
            "explainability_overlap_summary.tsv",

        summary=
            "results/deep_learning/comparison/"
            "comparison_summary.json"

    params:

        outdir=
            "results/deep_learning/comparison",

        top_features=
            config[
                "deep_learning"
            ][
                "explainability"
            ][
                "top_features"
            ]

    log:

        "logs/deep_learning/"
        "raw_vs_batch_corrected_comparison.log"

    benchmark:

        "benchmark/deep_learning/"
        "raw_vs_batch_corrected_comparison.txt"

    conda:

        "envs/deep_learning.yaml"

    shell:
        r"""
        mkdir -p "{params.outdir}"
        mkdir -p "$(dirname "{log}")"
        mkdir -p "$(dirname "{benchmark}")"

        set -euo pipefail

        python \
            scripts/python/deep_learning/compare_raw_corrected.py \
            --raw-metrics "{input.raw_metrics}" \
            --corrected-metrics "{input.corrected_metrics}" \
            --raw-predictions "{input.raw_predictions}" \
            --corrected-predictions "{input.corrected_predictions}" \
            --raw-nested "{input.raw_nested}" \
            --corrected-nested "{input.corrected_nested}" \
            --raw-importance "{input.raw_importance}" \
            --corrected-importance "{input.corrected_importance}" \
            --top-features {params.top_features} \
            --output "{params.outdir}" \
            > "{log}" 2>&1

        test -s "{output.metrics}"
        test -s "{output.predictions}"
        test -s "{output.agreement}"
        test -s "{output.nested}"
        test -s "{output.features}"
        test -s "{output.overlap}"
        test -s "{output.summary}"
        """