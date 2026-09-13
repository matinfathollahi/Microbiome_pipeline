rule permdisp_study_aware:
    input:
        distance=
            "results/export/beta/{metric}/distance-matrix.tsv",

        metadata=
            "metadata/sample_metadata.tsv"

    output:
        per_study=
            "results/statistics/permdisp/{metric}_Per_Study.tsv",

        summary=
            "results/statistics/permdisp/{metric}_Summary.tsv",

        eligibility=
            "results/statistics/permdisp/{metric}_Study_Eligibility.tsv"

    params:
        study_column=
            config["permdisp"]["study_column"],

        group_column=
            config["permdisp"]["metadata_column"],

        reference_group=
            config["permdisp"]["reference_group"],

        case_group=
            config["permdisp"]["case_group"],

        min_samples=
            config["permdisp"]["min_samples_per_group"],

        permutations=
            config["permdisp"]["permutations"],

        min_studies=
            config["permdisp"]["min_studies"],

        seed=
            config["permdisp"]["seed"]

    wildcard_constraints:
        metric=(
            "bray_curtis|"
            "jaccard|"
            "weighted_unifrac|"
            "unweighted_unifrac"
        )

    log:
        "logs/statistics/permdisp_{metric}_study_aware.log"

    benchmark:
        "benchmark/statistics/permdisp_{metric}_study_aware.txt"

    conda:
        "envs/r_batch.yaml"

    shell:
        r"""
        set -euo pipefail

        mkdir -p results/statistics/permdisp

        Rscript scripts/R/permdisp_study_aware.R \
            "{input.distance}" \
            "{input.metadata}" \
            "{wildcards.metric}" \
            "{output.per_study}" \
            "{output.summary}" \
            "{output.eligibility}" \
            "{params.study_column}" \
            "{params.group_column}" \
            "{params.reference_group}" \
            "{params.case_group}" \
            {params.min_samples} \
            {params.min_studies} \
            {params.permutations} \
            {params.seed} \
            > "{log}" 2>&1
        """