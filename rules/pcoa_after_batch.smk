rule pcoa_after_batch:

    input:
        distance="results/batch_effect/distance/bray_distance.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        directory("results/batch_correction/pcoa")

    log:
        "logs/batch_correction/pcoa_after.log"

    benchmark:
        "benchmark/batch_correction/pcoa_after.txt"

    conda:
        "envs/R.yaml"

    shell:
        r"""
        mkdir -p {output}
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/pcoa_after_batch.R \
            {input.distance} \
            {input.metadata} \
            {output} \
            > {log} 2>&1
        """