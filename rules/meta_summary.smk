rule meta_summary:

    input:

        meta=
            "results/meta_analysis/metafor/meta_results.tsv",

        bias=
            "results/meta_analysis/figures/funnel/publication_bias.tsv",

        taxonomy=
            "results/export/taxonomy/taxonomy.tsv"

    output:

        directory("results/meta_analysis/summary")

    log:

        "logs/meta_analysis/meta_summary.log"

    benchmark:

        "benchmark/meta_analysis/meta_summary.txt"

    conda:

        "envs/R.yaml"

    shell:

        r"""
        mkdir -p {output}
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/meta_summary.R \
            {input.meta} \
            {input.bias} \
            {input.taxonomy} \
            {output} \
            > {log} 2>&1
        """