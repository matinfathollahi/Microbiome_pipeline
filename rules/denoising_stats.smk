rule denoising_stats:

    input:

        stats=
            "results/qiime2/dada2/batches/{batch}/denoising_stats.qza"

    output:

        summary=
            "results/qiime2/denoising_stats/{batch}.qzv"

    log:

        "logs/qiime2/denoising_stats/{batch}.log"

    benchmark:

        "benchmark/qiime2/denoising_stats/{batch}.txt"

    conda:

        "envs/qiime2.yaml"

    shell:

        r"""
        mkdir -p $(dirname {output.summary})
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        bash scripts/bash/denoising_stats.sh \
            {input.stats} \
            {output.summary} \
            > {log} 2>&1
        """