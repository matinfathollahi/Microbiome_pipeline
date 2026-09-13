rule export_feature_table:
    input:
        "results/qiime2/dada2/feature_table.qza"

    output:
        "results/export/feature_table/feature-table.tsv"

    params:
        outdir="results/export/feature_table"

    log:
        "logs/export/feature_table.log"

    benchmark:
        "benchmark/export/feature_table.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        bash scripts/bash/export_feature_table.sh \
            {input} \
            {params.outdir} \
            > {log} 2>&1
        """