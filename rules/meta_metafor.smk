rule meta_metafor:
    input:
        "results/meta_analysis/effect_size/meta_effect_size.tsv"

    output:
        "results/meta_analysis/metafor/meta_results.tsv"

    params:
        min_studies=
            config[
                "meta_analysis"
            ][
                "min_studies"
            ]

    log:
        "logs/meta_analysis/meta_metafor.log"

    benchmark:
        "benchmark/meta_analysis/meta_metafor.txt"

    conda:
        "envs/R.yaml"

    shell:
        """
        mkdir -p results/meta_analysis/metafor
        mkdir -p $(dirname {log})

        Rscript scripts/R/meta_metafor.R \
            {input} \
            {output} \
            {params.min_studies} \
            > {log} 2>&1
        """