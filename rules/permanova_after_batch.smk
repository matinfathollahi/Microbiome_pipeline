rule permanova_after_batch:

    input:
        distance="results/batch_effect/distance/bray_distance.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        results="results/batch_correction/permanova/permanova_after.tsv"

    log:
        "logs/batch_correction/permanova_after.log"

    benchmark:
        "benchmark/batch_correction/permanova_after.txt"

    conda:
        "envs/R.yaml"

    params:
        variable=config["permanova"]["variable"],
        permutations=config["permanova"]["permutations"]

    shell:
        r"""
        mkdir -p $(dirname {output.results})
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/permanova_after_batch.R \
            {input.distance} \
            {input.metadata} \
            {params.variable} \
            {params.permutations} \
            {output.results} \
            > {log} 2>&1
        """