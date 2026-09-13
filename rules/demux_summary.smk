rule demux_summary:
    input:
        demux=
            "results/qiime2/import/{batch}/demux.qza"

    output:
        qzv=
            "results/qiime2/demux/{batch}.qzv"

    log:
        "logs/qiime2/demux_summary/{batch}.log"

    conda:
        "envs/qiime2.yaml"

    shell:
        r"""
        mkdir -p $(dirname {output.qzv})
        mkdir -p $(dirname {log})

        qiime demux summarize \
            --i-data {input.demux} \
            --o-visualization {output.qzv} \
            > {log} 2>&1
        """