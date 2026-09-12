rule emperor:

    input:
        core_metrics="results/qiime2/diversity/core_metrics",
        metadata="metadata/sample_metadata.tsv"

    output:
        "results/qiime2/emperor/{metric}_emperor.qzv"

    params:
        pcoa=lambda wildcards: (
            f"results/qiime2/diversity/core_metrics/"
            f"{wildcards.metric}_pcoa_results.qza"
        )

    wildcard_constraints:
        metric="bray_curtis|jaccard|weighted_unifrac|unweighted_unifrac"

    log:
        "logs/qiime2/emperor_{metric}.log"

    benchmark:
        "benchmark/qiime2/emperor_{metric}.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        mkdir -p results/qiime2/emperor

        qiime emperor plot \
            --i-pcoa {params.pcoa} \
            --m-metadata-file {input.metadata} \
            --o-visualization {output} \
            > {log} 2>&1
        """