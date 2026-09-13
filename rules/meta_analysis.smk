import pandas as pd


############################################################
# Discover eligible studies dynamically
############################################################

checkpoint discover_meta_studies:
    input:
        preflight=
            "results/qc/preflight/"
            "preflight_validation.json",

        metadata=
            "results/export/metadata/"
            "sample_metadata.tsv",

        table=
            "results/export/feature_table/"
            "feature-table.tsv"

    output:
        map=
            "results/meta_analysis/"
            "study_map.tsv",

        report=
            "results/meta_analysis/"
            "study_eligibility.tsv"

    params:
        study_column=
            config[
                "meta_analysis"
            ][
                "study_column"
            ],

        sample_column=
            config[
                "meta_analysis"
            ][
                "sample_column"
            ],

        group_column=
            config[
                "meta_analysis"
            ][
                "group_column"
            ],

        reference=
            config[
                "meta_analysis"
            ][
                "reference_group"
            ],

        case=
            config[
                "meta_analysis"
            ][
                "case_group"
            ],

        min_samples_per_group=
            config[
                "meta_analysis"
            ].get(
                "min_samples_per_group",
                2
            ),

        min_samples_per_study=
            config[
                "meta_analysis"
            ].get(
                "min_samples_per_study",
                4
            ),

        min_studies=
            config[
                "meta_analysis"
            ][
                "min_studies"
            ]

    log:
        "logs/meta_analysis/"
        "discover_studies.log"

    benchmark:
        "benchmark/meta_analysis/"
        "discover_studies.txt"

    conda:
        "envs/python.yaml"

    shell:
        r"""
        mkdir -p $(dirname {output.map})
        mkdir -p $(dirname {log})

        set -euo pipefail

        python scripts/python/discover_meta_studies.py \
            --metadata {input.metadata} \
            --feature-table {input.table} \
            --study-column "{params.study_column}" \
            --sample-column "{params.sample_column}" \
            --group-column "{params.group_column}" \
            --reference-group "{params.reference}" \
            --case-group "{params.case}" \
            --min-samples-per-group {params.min_samples_per_group} \
            --min-samples-per-study {params.min_samples_per_study} \
            --min-studies {params.min_studies} \
            --output {output.map} \
            --report {output.report} \
            > {log} 2>&1
        """
############################################################
# Dynamic list of eligible study-specific DESeq2 results
############################################################

def get_meta_study_results(wildcards):

    checkpoint_output = (

        checkpoints
        .discover_meta_studies
        .get()
        .output
        .map
    )


    study_map = pd.read_csv(
        checkpoint_output,
        sep="\t",
        dtype=str
    )


    required_columns = {
        "StudyID",
        "StudyValue"
    }


    missing_columns = (

        required_columns

        -

        set(
            study_map.columns
        )
    )


    if missing_columns:

        raise ValueError(
            "Study map missing columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )


    studies = (

        study_map[
            "StudyID"
        ]

        .dropna()

        .astype(str)

        .str.strip()
    )


    studies = studies[
        studies != ""
    ].tolist()


    if not studies:

        raise ValueError(
            "No eligible studies "
            "for meta-analysis."
        )


    min_studies = int(

        config[
            "meta_analysis"
        ][
            "min_studies"
        ]
    )


    if (
        len(studies)
        <
        min_studies
    ):

        raise ValueError(

            "Eligible studies below "
            "meta_analysis.min_studies: "

            f"{len(studies)} < "
            f"{min_studies}"
        )


    return expand(

        "results/meta_analysis/"
        "studies/{study}/"
        "deseq2/results.tsv",

        study=studies
    )

############################################################
# Prepare study-specific input
############################################################

rule prepare_meta_study:
    input:
        table=
            "results/export/feature_table/"
            "feature-table.tsv",

        metadata=
            "results/export/metadata/"
            "sample_metadata.tsv",

        study_map=
            "results/meta_analysis/"
            "study_map.tsv"

    output:
        table=
            "results/meta_analysis/"
            "studies/{study}/"
            "input/counts.tsv",

        metadata=
            "results/meta_analysis/"
            "studies/{study}/"
            "input/metadata.tsv"

    params:
        study_column=
            config[
                "meta_analysis"
            ][
                "study_column"
            ],

        sample_column=
            config[
                "meta_analysis"
            ][
                "sample_column"
            ]

    log:
        "logs/meta_analysis/"
        "{study}/prepare.log"

    benchmark:
        "benchmark/meta_analysis/"
        "{study}/prepare.txt"

    conda:
        "envs/python.yaml"

    shell:
        r"""
        mkdir -p $(dirname {log})

        python scripts/python/prepare_meta_study.py \
            --table {input.table} \
            --metadata {input.metadata} \
            --study-map {input.study_map} \
            --study-id "{wildcards.study}" \
            --study-column "{params.study_column}" \
            --sample-column "{params.sample_column}" \
            --output-table {output.table} \
            --output-metadata {output.metadata} \
            > {log} 2>&1
        """


############################################################
# DESeq2 independently within each study
############################################################

rule meta_study_deseq2:
    input:
        table=
            "results/meta_analysis/"
            "studies/{study}/"
            "input/counts.tsv",

        metadata=
            "results/meta_analysis/"
            "studies/{study}/"
            "input/metadata.tsv"

    output:
        "results/meta_analysis/"
        "studies/{study}/"
        "deseq2/results.tsv"

    params:
        sample_column=
            config[
                "meta_analysis"
            ][
                "sample_column"
            ],

        group_column=
            config[
                "meta_analysis"
            ][
                "group_column"
            ],

        reference=
            config[
                "meta_analysis"
            ][
                "reference_group"
            ],

        case=
            config[
                "meta_analysis"
            ][
                "case_group"
            ]

    log:
        "logs/meta_analysis/"
        "{study}/deseq2.log"

    benchmark:
        "benchmark/meta_analysis/"
        "{study}/deseq2.txt"

    conda:
        "envs/r_deseq2.yaml"

    shell:
        r"""
        mkdir -p $(dirname {output})
        mkdir -p $(dirname {log})

        Rscript scripts/R/meta_deseq2.R \
            {input.table} \
            {input.metadata} \
            "{params.sample_column}" \
            "{params.group_column}" \
            "{params.reference}" \
            "{params.case}" \
            "{wildcards.study}" \
            {output} \
            > {log} 2>&1
        """


############################################################
# Combine all discovered study effects
############################################################

rule meta_prepare:
    input:
        results=
            get_meta_study_results

    output:
        "results/meta_analysis/"
        "prepared/meta_prepared.tsv"

    log:
        "logs/meta_analysis/"
        "meta_prepare.log"

    benchmark:
        "benchmark/meta_analysis/"
        "meta_prepare.txt"

    conda:
        "envs/python.yaml"

    shell:
        r"""
        mkdir -p $(dirname {output})
        mkdir -p $(dirname {log})

        python scripts/python/combine_meta_results.py \
            --inputs {input.results} \
            --output {output} \
            > {log} 2>&1
        """