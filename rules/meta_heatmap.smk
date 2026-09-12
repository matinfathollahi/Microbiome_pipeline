rule meta_heatmap:

    input:
        study_effects=
            "results/meta_analysis/effect_size/meta_effect_size.tsv",

        meta_results=
            "results/meta_analysis/metafor/meta_results.tsv"

    output:
        directory(
            "results/meta_analysis/figures/heatmap"
        )

    log:
        "logs/meta_analysis/meta_heatmap.log"

    benchmark:
        "benchmark/meta_analysis/meta_heatmap.txt"

    conda:
        "envs/R.yaml"

    shell:
        r"""
        mkdir -p {output}
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/meta_heatmap.R \
            {input.study_effects} \
            {input.meta_results} \
            {output} \
            > {log} 2>&1
        """