rule reproducibility_report:
    input:
        config=
            "config/config.yaml",

        metadata=
            "metadata/sample_metadata.tsv",

        accessions=
            "metadata/accessions.tsv",

        classifier=
            "database/silva-138-99-classifier.qza",

        preflight=
            "results/qc/preflight/preflight_validation.json",

        publication=
            "results/publication/publication_summary.json"

    output:
        summary=
            "results/reproducibility/reproducibility_summary.json",

        versions=
            "results/reproducibility/software_versions.tsv",

        conda=
            "results/reproducibility/conda_packages.tsv",

        seeds=
            "results/reproducibility/random_seeds.tsv",

        inputs=
            "results/reproducibility/input_checksums.tsv",

        workflow=
            "results/reproducibility/workflow_checksums.tsv",

        config_snapshot=
            "results/reproducibility/config_used.yaml",

        git=
            "results/reproducibility/git_info.tsv"

    log:
        "logs/reproducibility/reproducibility.log"

    benchmark:
        "benchmark/reproducibility/reproducibility.txt"

    conda:
        "envs/python.yaml"

    shell:
        r"""
        mkdir -p results/reproducibility
        mkdir -p $(dirname {log})

        set -euo pipefail

        python scripts/python/generate_reproducibility_report.py \
            --project-root . \
            --config {input.config} \
            --metadata {input.metadata} \
            --accessions {input.accessions} \
            --classifier {input.classifier} \
            --preflight-report {input.preflight} \
            --publication-summary {input.publication} \
            --output results/reproducibility \
            > {log} 2>&1

        test -s {output.summary}
        test -s {output.versions}
        test -s {output.conda}
        test -s {output.seeds}
        test -s {output.inputs}
        test -s {output.workflow}
        test -s {output.config_snapshot}
        test -s {output.git}
        """