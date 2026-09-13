def optional_meta_input(path):
    if META_ENABLED:
        return path
    return []


def optional_predictive_sensitivity_input(path):
    if PREDICTIVE_BATCH_SENSITIVITY_ENABLED:
        return path
    return []


def optional_da_input(path):
    if DA_ENABLED and DA_PRIMARY_METHOD == "ancombc2":
        return path
    return []


def optional_aldex2_input(path):
    if ALDEX2_ENABLED:
        return path
    return []


def optional_maaslin2_input(path):
    if MAASLIN2_ENABLED:
        return path
    return []


def optional_supp_da_comparison_input(path):
    if SUPP_DA_ENABLED and DA_ENABLED:
        return path
    return []


PUBLICATION_BETA_METRICS = [
    "bray_curtis",
    "jaccard",
    "weighted_unifrac",
    "unweighted_unifrac"
]

rule publication_bundle:
    input:
        alpha=
            "results/figures/alpha",

        alpha_stats=
            "results/statistics/alpha",

        ancombc2=
            optional_da_input(
                "results/ancombc2/analysis_summary.tsv"
            ),

        aldex2=
            optional_aldex2_input(
                "results/aldex2/analysis_summary.tsv"
            ),

        maaslin2=
            optional_maaslin2_input(
                "results/maaslin2/group_results.tsv"
            ),

        maaslin2_significant=
            optional_maaslin2_input(
                "results/maaslin2/group_significant_results.tsv"
            ),

        supplementary_da_comparison=
            optional_supp_da_comparison_input(
                "results/supplementary_da/method_comparison.tsv"
            ),

        supplementary_da_primary=
            optional_supp_da_comparison_input(
                "results/supplementary_da/primary_robustness.tsv"
            ),

        lefse_consensus=
            "results/lefse/consensus/consensus_taxa.tsv",

        lefse_consensus_summary=
            "results/lefse/consensus/consensus_summary.tsv",

        lefse_per_study=
            "results/lefse/per_study/all_significant_taxa.tsv",

        lefse_eligibility=
            "results/lefse/per_study/study_eligibility.tsv",

        lefse_pooled_supplementary=
            "results/lefse/significant_taxa.tsv",

        lefse_pooled_figures_supplementary=
            "results/lefse/figures",

        selbal=
            "results/selbal/analysis/selbal_loso_summary.tsv",

        beta_permanova_study_aware=
            expand(
                "results/statistics/beta/{metric}_PERMANOVA.tsv",
                metric=PUBLICATION_BETA_METRICS
            ),

        beta_group_effect_study_aware=
            expand(
                "results/statistics/beta/{metric}_Group_Effect.tsv",
                metric=PUBLICATION_BETA_METRICS
            ),

        permdisp_study_aware=
            expand(
                "results/statistics/permdisp/{metric}_Summary.tsv",
                metric=PUBLICATION_BETA_METRICS
            ),

        meta_results=
            optional_meta_input(
                "results/meta_analysis/metafor/meta_results.tsv"
            ),

        meta_forest=
            optional_meta_input(
                "results/meta_analysis/figures/forest"
            ),

        meta_funnel=
            optional_meta_input(
                "results/meta_analysis/figures/funnel/publication_bias.tsv"
            ),

        meta_heatmap=
            optional_meta_input(
                "results/meta_analysis/figures/heatmap"
            ),

        meta_summary=
            optional_meta_input(
                "results/meta_analysis/summary"
            ),

        ml=
            "results/machine_learning/final/final_test_metrics.tsv",

        dl=
            "results/deep_learning/nested_cv/nested_summary.json",
        dl_final=
            "results/deep_learning/final/final_summary.json",

        ml_batch_corrected=
            optional_predictive_sensitivity_input(
                "results/machine_learning_batch_corrected/"
                "final/final_test_metrics.tsv"
            ),

        dl_batch_corrected_final=
            optional_predictive_sensitivity_input(
                "results/deep_learning/batch_corrected/"
                "final/final_summary.json"
            ),

        dl_batch_corrected_explainability=
            optional_predictive_sensitivity_input(
                "results/deep_learning/batch_corrected/"
                "explainability/explainability_summary.json"
            ),

        dl_batch_corrected_visualization=
            optional_predictive_sensitivity_input(
                "results/deep_learning/batch_corrected/"
                "visualization/visualization_summary.json"
            ),

        dl_raw_vs_corrected_comparison=
            optional_predictive_sensitivity_input(
                "results/deep_learning/comparison/"
                "comparison_summary.json"
            ),

        batch_diagnostics=
            "results/batch_effect/diagnostics/summary/batch_diagnostics_summary.tsv",

        batch_confounding=
            "results/batch_effect/confounding",

        explainability=
            "results/deep_learning/explainability/explainability_summary.json",

        visualization=
            "results/deep_learning/visualization/visualization_summary.json"

    output:
        manifest=
            "results/publication/manifest.tsv",

        summary=
            "results/publication/publication_summary.json"

    params:
        predictive_sensitivity_flag=
            (
                "--include-predictive-sensitivity"
                if PREDICTIVE_BATCH_SENSITIVITY_ENABLED
                else ""
            )

    log:
        "logs/publication/publication.log"

    benchmark:
        "benchmark/publication/publication.txt"

    conda:
        "envs/ml.yaml"

    shell:
        r"""
        mkdir -p results/publication
        mkdir -p $(dirname {log})

        set -euo pipefail

        PYTHONPATH=scripts/python \
        python -m deep_learning.publication.build_publication_bundle \
            --output results/publication \
            {params.predictive_sensitivity_flag} \
            > {log} 2>&1

        test -s {output.manifest}
        test -s {output.summary}
        """