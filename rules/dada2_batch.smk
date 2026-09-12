rule dada2_batch:

    input:
        preflight="results/qc/preflight/preflight_validation.json",
        demux="results/qiime2/import/{batch}/demux.qza"

    output:
        table="results/qiime2/dada2/batches/{batch}/feature_table.qza",
        repseq="results/qiime2/dada2/batches/{batch}/representative_sequences.qza",
        stats="results/qiime2/dada2/batches/{batch}/denoising_stats.qza"

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
        "logs/qiime2/dada2/{batch}.log"

    benchmark:
        "benchmark/qiime2/dada2/{batch}.txt"

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


rule merge_dada2:

    input:
        preflight="results/qc/preflight/preflight_validation.json",

        tables=expand(
            "results/qiime2/dada2/batches/{batch}/feature_table.qza",
            batch=DENOISE_BATCHES
        ),

        repseqs=expand(
            "results/qiime2/dada2/batches/{batch}/representative_sequences.qza",
            batch=DENOISE_BATCHES
        )

    output:
        table="results/qiime2/dada2/feature_table.qza",
        repseq="results/qiime2/dada2/representative_sequences.qza"

    log:
        "logs/qiime2/dada2/merge.log"

    benchmark:
        "benchmark/qiime2/dada2/merge.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        r"""
        mkdir -p $(dirname {output.table})
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        {
            qiime feature-table merge \
                --i-tables {input.tables} \
                --o-merged-table {output.table}

            qiime feature-table merge-seqs \
                --i-data {input.repseqs} \
                --o-merged-data {output.repseq}
        } > {log} 2>&1
        """