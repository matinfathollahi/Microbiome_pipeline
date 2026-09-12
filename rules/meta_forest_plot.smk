rule meta_forest_plot:

    input:
        effect_size="results/meta_analysis/effect_size/meta_effect_size.tsv"

    output:
        directory("results/meta_analysis/figures/forest")

    log:
        "logs/meta_analysis/meta_forest_plot.log"

    benchmark:
        "benchmark/meta_analysis/meta_forest_plot.txt"

    conda:
        "envs/R.yaml"

    shell:
        r"""
        mkdir -p {output}
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/meta_forest_plot.R \
            {input.effect_size} \
            {output} \
            > {log} 2>&1
        """