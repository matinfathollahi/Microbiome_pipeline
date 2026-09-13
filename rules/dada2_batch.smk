def dada2_batch_param(wildcards, key):
    overrides = config["dada2"].get("batch_overrides", {}) or {}
    batch_overrides = overrides.get(wildcards.batch, {}) or {}
    return batch_overrides.get(key, config["dada2"][key])


rule dada2_batch:
    input:
        preflight="results/qc/preflight/preflight_validation.json",
        demux="results/qiime2/import/{batch}/demux.qza"

    output:
        table="results/qiime2/dada2/batches/{batch}/feature_table.qza",
        repseq="results/qiime2/dada2/batches/{batch}/representative_sequences.qza",
        stats="results/qiime2/dada2/batches/{batch}/denoising_stats.qza"

    params:
        trim_left_f=lambda wc: dada2_batch_param(wc, "trim_left_f"),
        trim_left_r=lambda wc: dada2_batch_param(wc, "trim_left_r"),
        trunc_len_f=lambda wc: dada2_batch_param(wc, "trunc_len_f"),
        trunc_len_r=lambda wc: dada2_batch_param(wc, "trunc_len_r"),
        max_ee_f=lambda wc: dada2_batch_param(wc, "max_ee_f"),
        max_ee_r=lambda wc: dada2_batch_param(wc, "max_ee_r"),
        trunc_q=lambda wc: dada2_batch_param(wc, "trunc_q"),
        chimera_method=lambda wc: dada2_batch_param(wc, "chimera_method"),
        pooling=lambda wc: dada2_batch_param(wc, "pooling"),
        min_overlap=lambda wc: dada2_batch_param(wc, "min_overlap")

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

        set -euo pipefail

        {{
            qiime feature-table merge \
                --i-tables {input.tables} \
                --o-merged-table {output.table}

            qiime feature-table merge-seqs \
                --i-data {input.repseqs} \
                --o-merged-data {output.repseq}
        }} > {log} 2>&1
        """