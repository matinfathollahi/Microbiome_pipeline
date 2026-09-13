rule confounding_check:
    input:
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        directory("results/batch_effect/confounding")

    params:
        batch=config["batch_correction"]["batch_variable"],
        variables=",".join(config["confounding"]["variables"])

    log:
        "logs/batch_effect/confounding.log"

    benchmark:
        "benchmark/batch_effect/confounding.txt"

    conda:
        "envs/r_batch.yaml"

    shell:
        """
        mkdir -p {output}

        Rscript scripts/R/confounding_check.R \
            {input.metadata} \
            "{params.batch}" \
            "{params.variables}" \
            {output} \
            > {log} 2>&1
        """