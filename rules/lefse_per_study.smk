rule lefse_per_study_consensus:

    input:

        table=
            "results/export/feature_table/feature-table.tsv",

        taxonomy=
            "results/export/taxonomy/taxonomy.tsv",

        metadata=
            "results/export/metadata/sample_metadata.tsv"

    output:

        by_study=
            directory(
                "results/lefse/by_study"
            ),

        eligibility=
            "results/lefse/per_study/study_eligibility.tsv",

        all_significant=
            "results/lefse/per_study/all_significant_taxa.tsv",

        directory_map=
            "results/lefse/per_study/study_directory_map.tsv",

        consensus_all=
            "results/lefse/consensus/consensus_all.tsv",

        consensus=
            "results/lefse/consensus/consensus_taxa.tsv",

        summary=
            "results/lefse/consensus/consensus_summary.tsv"

    params:

        class_column=
            config["lefse"]["class_column"],

        study_column=
            config["lefse"]["study_column"],

        reference_group=
            config["lefse"]["reference_group"],

        case_group=
            config["lefse"]["case_group"],

        min_samples=
            config["lefse"]["min_samples_per_group"],

        min_studies=
            config["lefse"]["min_studies"],

        normalization=
            config["lefse"]["normalization"],

        alpha=
            config["lefse"]["alpha"],

        lda=
            config["lefse"]["lda_threshold"],

        min_significant_studies=
            config["lefse"][
                "consensus"
            ][
                "min_significant_studies"
            ],

        min_direction_consistency=
            config["lefse"][
                "consensus"
            ][
                "min_direction_consistency"
            ]

    log:

        "logs/lefse/lefse_per_study.log"

    benchmark:

        "benchmark/lefse/lefse_per_study.txt"

    conda:

        "envs/lefse.yaml"

    shell:

        r"""
        set -euo pipefail

        mkdir -p results/lefse/per_study
        mkdir -p results/lefse/consensus
        mkdir -p logs/lefse
        mkdir -p benchmark/lefse

        python scripts/python/run_lefse_per_study.py \
            --table "{input.table}" \
            --taxonomy "{input.taxonomy}" \
            --metadata "{input.metadata}" \
            --outdir "results/lefse" \
            --class-column "{params.class_column}" \
            --study-column "{params.study_column}" \
            --reference-group "{params.reference_group}" \
            --case-group "{params.case_group}" \
            --min-samples-per-group {params.min_samples} \
            --min-studies {params.min_studies} \
            --normalization {params.normalization} \
            --alpha {params.alpha} \
            --lda-threshold {params.lda} \
            --min-significant-studies {params.min_significant_studies} \
            --min-direction-consistency {params.min_direction_consistency} \
            > "{log}" 2>&1
        """