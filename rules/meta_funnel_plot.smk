rule meta_funnel_plot:

    input:
        effect_size=
            "results/meta_analysis/effect_size/meta_effect_size.tsv"

    output:
        bias=
            "results/meta_analysis/figures/funnel/publication_bias.tsv"

    params:
        outdir=
            "results/meta_analysis/figures/funnel"

    log:
        "logs/meta_analysis/meta_funnel_plot.log"

    benchmark:
        "benchmark/meta_analysis/meta_funnel_plot.txt"

    conda:
        "envs/R.yaml"

    shell:
        r"""
        mkdir -p {params.outdir}
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        Rscript scripts/R/meta_funnel_plot.R \
            {input.effect_size} \
            {params.outdir} \
            > {log} 2>&1

        test -s {output.bias}
        """