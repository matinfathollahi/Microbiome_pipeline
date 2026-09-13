rule export_beta_distance_study_aware:
    input:
        core_metrics=
            "results/qiime2/diversity/core_metrics"

    output:
        distance=
            "results/export/beta/{metric}/distance-matrix.tsv"

    params:
        distance=lambda wildcards, input: (
            f"{input.core_metrics}/"
            f"{wildcards.metric}_distance_matrix.qza"
        )

    wildcard_constraints:
        metric=(
            "bray_curtis|"
            "jaccard|"
            "weighted_unifrac|"
            "unweighted_unifrac"
        )

    log:
        "logs/qiime2/export_beta_distance_{metric}.log"

    benchmark:
        "benchmark/qiime2/export_beta_distance_{metric}.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        r"""
        set -euo pipefail

        mkdir -p "$(dirname "{output.distance}")"

        TMP=$(mktemp -d)

        trap 'rm -rf "$TMP"' EXIT

        qiime tools export \
            --input-path "{params.distance}" \
            --output-path "$TMP" \
            > "{log}" 2>&1

        if [ ! -f "$TMP/distance-matrix.tsv" ]; then
            echo "Exported distance-matrix.tsv not found." >> "{log}"
            exit 1
        fi

        cp \
            "$TMP/distance-matrix.tsv" \
            "{output.distance}"
        """


rule beta_permanova_study_aware:
    input:
        distance=
            "results/export/beta/{metric}/distance-matrix.tsv",

        metadata=
            "metadata/sample_metadata.tsv"

    output:
        result=
            "results/statistics/beta/{metric}_PERMANOVA.tsv",

        group_effect=
            "results/statistics/beta/{metric}_Group_Effect.tsv",

        eligibility=
            "results/statistics/beta/{metric}_Study_Eligibility.tsv"

    params:
        study_column=
            config["beta"]["study_column"],

        group_column=
            config["beta"]["metadata_column"],

        reference_group=
            config["beta"]["reference_group"],

        case_group=
            config["beta"]["case_group"],

        min_samples=
            config["beta"]["min_samples_per_group"],

        min_studies=
            config["beta"]["min_studies"],

        permutations=
            config["beta"]["permutations"],

        seed=
            config["beta"]["seed"]

    wildcard_constraints:
        metric=(
            "bray_curtis|"
            "jaccard|"
            "weighted_unifrac|"
            "unweighted_unifrac"
        )

    log:
        "logs/statistics/beta_{metric}_study_aware.log"

    benchmark:
        "benchmark/statistics/beta_{metric}_study_aware.txt"

    conda:
        "envs/r_batch.yaml"

    shell:
        """
        mkdir -p results/statistics/beta

        Rscript scripts/R/permanova_study_aware.R \
            {input.distance} \
            {input.metadata} \
            "{wildcards.metric}" \
            {output.result} \
            {output.group_effect} \
            {output.eligibility} \
            "{params.study_column}" \
            "{params.group_column}" \
            "{params.reference_group}" \
            "{params.case_group}" \
            {params.min_samples} \
            {params.min_studies} \
            {params.permutations} \
            {params.seed} \
            > {log} 2>&1
        """