rule dada2:

    input:
        demux="results/qiime2/import/demux.qza"

    output:
        table="results/qiime2/dada2/feature_table.qza",
        repseq="results/qiime2/dada2/representative_sequences.qza",
        stats="results/qiime2/dada2/denoising_stats.qza"

    params:
        trim_left_f=config["dada2"]["trim_left_f"],
        trim_left_r=config["dada2"]["trim_left_r"],
        trunc_len_f=config["dada2"]["trunc_len_f"],
        trunc_len_r=config["dada2"]["trunc_len_r"],
        max_ee_f=config["dada2"]["max_ee_f"],
        max_ee_r=config["dada2"]["max_ee_r"],
        trunc_q=config["dada2"]["trunc_q"],
        chimera_method=config["dada2"]["chimera_method"],
        pooling=config["dada2"]["pooling"],
        min_overlap=config["dada2"]["min_overlap"]

    log:
        "logs/qiime2/dada2.log"

    benchmark:
        "benchmark/qiime2/dada2.txt"

    conda:
        "envs/qiime2.yaml"

    threads:
        config["dada2"]["threads"]

    shell:
        r"""
        mkdir -p $(dirname {output.table})
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        bash scripts/bash/dada2.sh \
            {input.demux} \
            {output.table} \
            {output.repseq} \
            {output.stats} \
            {threads} \
            {params.trim_left_f} \
            {params.trim_left_r} \
            {params.trunc_len_f} \
            {params.trunc_len_r} \
            {params.max_ee_f} \
            {params.max_ee_r} \
            {params.trunc_q} \
            {params.chimera_method} \
            {params.pooling} \
            {params.min_overlap} \
            > {log} 2>&1
        """