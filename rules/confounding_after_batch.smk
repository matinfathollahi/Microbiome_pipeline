rule confounding_after_batch:
    input:
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        directory("results/batch_correction/confounding")

    params:
        batch=config["batch_correction"]["batch_variable"],
        variables=",".join(config["confounding"]["variables"])

    log:
        "logs/batch_correction/confounding.log"

    benchmark:
        "benchmark/batch_correction/confounding.txt"

    conda:
        "envs/R.yaml"

    shell:
        r"""
        mkdir -p {output}
        mkdir -p $(dirname {log})

        set -euo pipefail

        Rscript scripts/R/confounding_after_batch.R \
            {input.metadata} \
            {params.batch} \
            "{params.variables}" \
            {output} \
            > {log} 2>&1
        """