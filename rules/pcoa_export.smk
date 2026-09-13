DISTANCE_METRICS = [
    "bray_curtis",
    "jaccard",
    "weighted_unifrac",
    "unweighted_unifrac"
]

rule export_pcoa:
    input:
        pcoa="results/qiime2/diversity/core_metrics/{metric}_pcoa_results.qza"

    output:
        directory("results/export/pcoa/{metric}")

    log:
        "logs/export/pcoa/{metric}.log"

    benchmark:
        "benchmark/export/pcoa/{metric}.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        bash scripts/bash/export_pcoa.sh \
            {input.pcoa} \
            {output} \
            > {log} 2>&1
        """