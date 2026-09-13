rule selbal:
    input:
        table=
            "results/export/feature_table/feature-table.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:
        summary=
            "results/selbal/analysis/selbal_loso_summary.tsv",

        predictions=
            "results/selbal/analysis/loso_predictions.tsv",

        fold_metrics=
            "results/selbal/analysis/loso_fold_metrics.tsv",

        fold_balances=
            "results/selbal/analysis/loso_fold_balances.tsv",

        stability=
            "results/selbal/analysis/taxon_stability.tsv",

        eligibility=
            "results/selbal/analysis/study_eligibility.tsv",

        final_balance=
            "results/selbal/analysis/final_balance.tsv",

        final_model=
            "results/selbal/analysis/final_model.rds",

        final_features=
            "results/selbal/analysis/final_prefilter_features.tsv",

        roc=
            "results/selbal/analysis/LOSO_ROC.pdf"

    params:
        study_column=
            config["selbal"]["study_column"],

        group_column=
            config["selbal"]["group_column"],

        reference_group=
            config["selbal"]["reference_group"],

        case_group=
            config["selbal"]["case_group"],

        min_samples=
            config["selbal"]["min_samples_per_group"],

        min_studies=
            config["selbal"]["min_studies"],

        min_count=
            config["filtering"]["min_count"],

        prevalence=
            config["filtering"]["prevalence"],

        inner_folds=
            config["selbal"]["inner_folds"],

        inner_iterations=
            config["selbal"]["inner_iterations"],

        max_features=
            config["selbal"]["max_features"],

        seed=
            config["selbal"]["seed"],

        zero_replacement=
            config["selbal"]["zero_replacement"],

        opt_criterion=
            config["selbal"]["opt_criterion"]

    log:
        "logs/selbal/selbal_loso.log"

    benchmark:
        "benchmark/selbal/selbal_loso.txt"

    conda:
        "envs/r_selbal.yaml"

    shell:
        r"""
        set -euo pipefail

        mkdir -p results/selbal/analysis
        mkdir -p logs/selbal
        mkdir -p benchmark/selbal

        Rscript scripts/R/selbal.R \
            "{input.table}" \
            "{input.metadata}" \
            "results/selbal/analysis" \
            "{params.study_column}" \
            "{params.group_column}" \
            "{params.reference_group}" \
            "{params.case_group}" \
            {params.min_samples} \
            {params.min_studies} \
            {params.min_count} \
            {params.prevalence} \
            {params.inner_folds} \
            {params.inner_iterations} \
            {params.max_features} \
            {params.seed} \
            "{params.zero_replacement}" \
            "{params.opt_criterion}" \
            > "{log}" 2>&1
        """