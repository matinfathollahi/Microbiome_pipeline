rule meta_effect_size:

    input:
        "results/meta_analysis/prepared/meta_prepared.tsv"

    output:
        "results/meta_analysis/effect_size/meta_effect_size.tsv"

    log:
        "logs/meta_analysis/meta_effect_size.log"

    benchmark:
        "benchmark/meta_analysis/meta_effect_size.txt"

    conda:
        "envs/R.yaml"

    shell:
        """
        mkdir -p results/meta_analysis/effect_size

        Rscript scripts/R/meta_effect_size.R \
            {input} \
            {output} \
            > {log} 2>&1
        """