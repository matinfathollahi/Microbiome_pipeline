
configfile: "config/config.yaml"


META_ENABLED = bool(
    config.get("meta_analysis", {}).get("enabled", True)
)

META_TARGETS = (
    [
        "results/meta_analysis/metafor/meta_results.tsv",
        "results/meta_analysis/figures/forest",
        "results/meta_analysis/figures/funnel/publication_bias.tsv",
        "results/meta_analysis/figures/heatmap",
        "results/meta_analysis/summary",
    ]
    if META_ENABLED
    else []
)


DA_CFG = config.get("differential_abundance", {})
DA_ENABLED = bool(DA_CFG.get("enabled", True))
DA_PRIMARY_METHOD = DA_CFG.get("primary_method", "ancombc2")

SUPP_DA_CFG = config.get("supplementary_differential_abundance", {})
SUPP_DA_ENABLED = bool(SUPP_DA_CFG.get("enabled", True))
ALDEX2_ENABLED = SUPP_DA_ENABLED and bool(
    SUPP_DA_CFG.get("aldex2", {}).get("enabled", True)
)
MAASLIN2_ENABLED = SUPP_DA_ENABLED and bool(
    SUPP_DA_CFG.get("maaslin2", {}).get("enabled", True)
)

ANCOMBC2_TARGETS = (
    [
        "results/ancombc2/all_results.tsv",
        "results/ancombc2/significant_results.tsv",
        "results/ancombc2/study_eligibility.tsv",
        "results/ancombc2/analysis_summary.tsv",
    ]
    if DA_ENABLED and DA_PRIMARY_METHOD == "ancombc2"
    else []
)

ALDEX2_TARGETS = (
    [
        "results/aldex2/group_results.tsv",
        "results/aldex2/significant_results.tsv",
        "results/aldex2/study_eligibility.tsv",
        "results/aldex2/analysis_summary.tsv",
    ]
    if ALDEX2_ENABLED
    else []
)

MAASLIN2_TARGETS = (
    [
        "results/maaslin2/group_results.tsv",
        "results/maaslin2/group_significant_results.tsv",
        "results/maaslin2/study_eligibility.tsv",
        "results/maaslin2/analysis_summary.tsv",
    ]
    if MAASLIN2_ENABLED
    else []
)

SUPPLEMENTARY_DA_COMPARISON_TARGETS = (
    [
        "results/supplementary_da/method_comparison.tsv",
        "results/supplementary_da/primary_robustness.tsv",
    ]
    if SUPP_DA_ENABLED and DA_ENABLED
    else []
)


PREDICTIVE_BATCH_SENSITIVITY_ENABLED = bool(
    config.get(
        "batch_correction",
        {}
    )
    .get(
        "predictive_sensitivity",
        {}
    )
    .get(
        "enabled",
        True
    )
)


PREDICTIVE_BATCH_SENSITIVITY_TARGETS = (
    [
        "results/machine_learning_batch_corrected/dataset.tsv",

        "results/machine_learning_batch_corrected/train.tsv",

        "results/machine_learning_batch_corrected/test.tsv",

        "results/machine_learning_batch_corrected/nested_cv",

        "results/machine_learning_batch_corrected/"
        "optuna/best_model.json",

        "results/machine_learning_batch_corrected/"
        "feature_selection/consensus_features.tsv",

        "results/machine_learning_batch_corrected/"
        "final/final_test_metrics.tsv",

        "results/machine_learning_batch_corrected/"
        "final/final_test_predictions.tsv",

        "results/machine_learning_batch_corrected/"
        "final/final_model.joblib",
    ]

    if PREDICTIVE_BATCH_SENSITIVITY_ENABLED

    else []
)



DL_BATCH_SENSITIVITY_TARGETS = (
    [
        # Prepared corrected DL data
        "results/deep_learning/batch_corrected/"
        "data/train_features.tsv",

        "results/deep_learning/batch_corrected/"
        "data/train_labels.tsv",

        "results/deep_learning/batch_corrected/"
        "data/train_groups.tsv",

        # Corrected DL nested CV
        "results/deep_learning/batch_corrected/"
        "nested_cv/nested_summary.json",

        # Corrected DL final evaluation
        "results/deep_learning/batch_corrected/"
        "final/final_test_metrics.tsv",

        "results/deep_learning/batch_corrected/"
        "final/final_summary.json",

        # Corrected DL visualization
        "results/deep_learning/batch_corrected/"
        "visualization/visualization_summary.json",

        "results/deep_learning/batch_corrected/"
        "visualization/visualization_status.tsv",

        # Corrected DL explainability
        "results/deep_learning/batch_corrected/"
        "explainability/explainability_summary.json",

        # Raw vs corrected sensitivity comparison
        "results/deep_learning/comparison/"
        "final_metrics_comparison.tsv",

        "results/deep_learning/comparison/"
        "explainability_overlap_summary.tsv",

        "results/deep_learning/comparison/"
        "comparison_summary.json",
    ]

    if PREDICTIVE_BATCH_SENSITIVITY_ENABLED

    else []
)

include: "rules/preflight_validation.smk"
include: "rules/download.smk"
include: "rules/validate_sra.smk"
include: "rules/convert.smk"
include: "rules/compress.smk"
include: "rules/validate_fastq.smk"
include: "rules/manifest.smk"

include: "rules/qiime2_import.smk"
include: "rules/optimization.smk"
include: "rules/demux_summary.smk"
include: "rules/denoising_stats.smk"
include: "rules/permdisp.smk"
include: "rules/permdisp_study_aware.smk"
include: "rules/beta_diversity.smk"
include: "rules/beta_study_aware.smk"
include: "rules/emperor.smk"
include: "rules/export_alpha.smk"
include: "rules/alpha_plots.smk"
include: "rules/alpha_statistics.smk"
include: "rules/export_feature_table.smk"
include: "rules/export_taxonomy.smk"
include: "rules/ancombc.smk"
include: "rules/aldex2.smk"
include: "rules/maaslin2.smk"
include: "rules/supplementary_da_comparison.smk"
include: "rules/export_sequences.smk"
include: "rules/export_tree.smk"
include: "rules/export_metadata.smk"
include: "rules/low_abundance_filter.smk"
include: "rules/low_prevalence_filter.smk"
include: "rules/zero_replacement.smk"

include: "rules/selbal.smk"

include: "rules/clr_normalization.smk"
include: "rules/batch_correction.smk"
include: "rules/predictive_batch_correction.smk"
include: "rules/confounding_check.smk"
include: "rules/batch_before_after_diagnostics.smk"
include: "rules/prepare_ml_dataset.smk"
include: "rules/prepare_ml_dataset_batch_corrected.smk"
include: "rules/ml_split_batch_corrected.smk"
include: "rules/machine_learning/train_test_split.smk"
include: "rules/predictive_preprocessing.smk"
include: "rules/predictive_preprocessing_batch_corrected.smk"
include: "rules/variance_filter.smk"
include: "rules/boruta_selection.smk"
include: "rules/machine_learning/elasticnet_selection.smk"
include: "rules/machine_learning/rf_selection.smk"
include: "rules/machine_learning/consensus_selection.smk"
include: "rules/feature_selection_batch_corrected.smk"
include: "rules/machine_learning/nested_cv.smk"
include: "rules/nested_cv_batch_corrected.smk"
include: "rules/machine_learning/hyperparameter_optimization.smk"
include: "rules/machine_learning/hyperparameter_optimization_batch_corrected.smk"
include: "rules/machine_learning/final_model_evaluation_batch_corrected.smk"
include: "rules/machine_learning/final_model_evaluation.smk"
include: "rules/deep_learning.smk"
include: "rules/deep_learning_batch_corrected.smk"
include: "rules/deep_learning_comparison.smk"
include: "rules/deep_learning_final_evaluation.smk"
include: "rules/deep_learning_visualization.smk"
include: "rules/deep_learning_explainability.smk"
include: "rules/lefse_visualization.smk"
include: "rules/lefse.smk"
include: "rules/lefse_per_study.smk"
include: "rules/meta_analysis.smk"
include: "rules/meta_effect_size.smk"
include: "rules/meta_metafor.smk"
include: "rules/meta_forest_plot.smk"
include: "rules/meta_funnel_plot.smk"
include: "rules/meta_heatmap.smk"
include: "rules/meta_summary.smk"
include: "rules/publication.smk"
#include: "rules/dada2.smk"
include: "rules/dada2_batch.smk"
include: "rules/taxonomy.smk"
include: "rules/phylogeny.smk"
include: "rules/core_diversity.smk"
include: "rules/alpha_diversity.smk"
include: "rules/reproducibility.smk"



rule all:
    input:
        expand(
            "results/qiime2/demux/{batch}.qzv",
            batch=DENOISE_BATCHES
        ),
        "results/qc/preflight/preflight_validation.json",

        "results/export/feature_table/feature-table.tsv",

        expand(
            "results/qiime2/denoising_stats/{batch}.qzv",
            batch=DENOISE_BATCHES
        ),

        "results/figures/alpha",

        "results/statistics/alpha",

        "results/export/taxonomy/taxonomy.tsv",



        SUPPLEMENTARY_DA_COMPARISON_TARGETS,

        "results/export/sequences",
        "results/export/tree",
        "results/machine_learning/optuna/best_model.json",
        "results/machine_learning/optuna/model_summary.tsv",
        "results/machine_learning/optuna/outer_fold_results.tsv",




        "results/machine_learning/final/final_test_metrics.tsv",
        "results/export/metadata/sample_metadata.tsv",

        ANCOMBC2_TARGETS,
        PREDICTIVE_BATCH_SENSITIVITY_TARGETS,

        DL_BATCH_SENSITIVITY_TARGETS,

        # Supplementary differential abundance - ALDEx2
        ALDEX2_TARGETS,

        # Supplementary differential abundance - MaAsLin2
        MAASLIN2_TARGETS,


        "results/lefse/significant_taxa.tsv",

        "results/lefse/consensus/consensus_taxa.tsv",

        "results/lefse/consensus/consensus_summary.tsv",

        "results/lefse/per_study/all_significant_taxa.tsv",
        "results/batch_effect/corrected/feature_table_corrected.tsv",

        "results/lefse/figures",
        "results/deep_learning/nested_cv/nested_summary.json",

        "results/deep_learning/final/final_test_metrics.tsv",

        "results/deep_learning/final/final_summary.json",

        "results/deep_learning/explainability/explainability_summary.json",

        "results/selbal/analysis/selbal_loso_summary.tsv",

        "results/selbal/analysis/loso_predictions.tsv",

        "results/selbal/analysis/taxon_stability.tsv",

        "results/selbal/analysis/final_balance.tsv",

        META_TARGETS,

        "results/deep_learning/visualization/visualization_summary.json",

        "results/publication/publication_summary.json",



        "results/batch_effect/confounding",


        "results/batch_effect/diagnostics/summary/batch_diagnostics_summary.tsv",

        "results/batch_effect/diagnostics/summary/batch_diagnostics_comparison.pdf",


        expand(
            "results/export/alpha/{metric}/alpha-diversity.tsv",
            metric=[
                "faith_pd",
                "shannon",
                "evenness",
                "observed_features"
            ]
        ),

        expand(
            "results/qiime2/beta/{metric}_permdisp.qzv",
            metric=[
                "bray_curtis",
                "jaccard",
                "weighted_unifrac",
                "unweighted_unifrac"
            ]
        ),

        expand(
            "results/statistics/permdisp/{metric}_Summary.tsv",
            metric=[
                "bray_curtis",
                "jaccard",
                "weighted_unifrac",
                "unweighted_unifrac"
            ]
        ),

        expand(
            "results/qiime2/beta/{metric}_permanova.qzv",
            metric=[
                "bray_curtis",
                "jaccard",
                "weighted_unifrac",
                "unweighted_unifrac"
            ]
        ),


        expand(
            "results/statistics/beta/{metric}_Group_Effect.tsv",
            metric=[
                "bray_curtis",
                "jaccard",
                "weighted_unifrac",
                "unweighted_unifrac"
            ]
        ),


        expand(
            "results/qiime2/emperor/{metric}_emperor.qzv",
            metric=[
                "bray_curtis",
                "jaccard",
                "weighted_unifrac",
                "unweighted_unifrac"
            ]
        ),


        expand(
            "results/qiime2/alpha/{metric}_significance.qzv",
            metric=[
                "faith_pd",
                "shannon",
                "evenness",
                "observed_features"
            ]
        ),
        
        "results/reproducibility/reproducibility_summary.json",

