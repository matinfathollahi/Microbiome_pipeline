rule beta_plots:

    input:
        pcoa="results/export/pcoa/bray_curtis/ordination.txt",
        metadata="metadata/sample_metadata.tsv"

    output:
        figure="results/figures/beta/bray_curtis_pcoa.pdf"

    log:
        "logs/R/beta_plots.log"

    benchmark:
        "benchmark/R/beta_plots.txt"

    conda:
        "envs/R.yaml"

    shell:
        r"""
        mkdir -p $(dirname {output.figure})
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/beta_plots.R \
            {input.pcoa} \
            {input.metadata} \
            {output.figure} \
            > {log} 2>&1
        """