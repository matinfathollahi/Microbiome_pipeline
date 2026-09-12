rule preflight_validation:

    input:
        config="config/config.yaml"

    output:
        validation_json="results/qc/preflight/preflight_validation.json",
        checks="results/qc/preflight/preflight_checks.tsv"

    params:
        metadata="metadata/sample_metadata.tsv",
        accessions="metadata/accessions.tsv",
        classifier="database/silva-138-99-classifier.qza"

    log:
        "logs/qc/preflight_validation.log"

    benchmark:
        "benchmark/qc/preflight_validation.txt"

    conda:
        "envs/python.yaml"

    shell:
        r"""
        mkdir -p results/qc/preflight
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        python scripts/python/preflight_validate.py \
            --config {input.config} \
            --metadata {params.metadata} \
            --accessions {params.accessions} \
            --classifier {params.classifier} \
            --json-output {output.validation_json} \
            --tsv-output {output.checks} \
            > {log} 2>&1
        """