rule feature_table_summary:
    input:
        table="results/qiime2/dada2/feature_table.qza",
        metadata="metadata/sample_metadata.tsv"

    output:
        summary="results/qiime2/feature_table/feature_table.qzv"

    log:
        "logs/qiime2/feature_table_summary.log"

    benchmark:
        "benchmark/qiime2/feature_table_summary.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        mkdir -p results/qiime2/feature_table

        qiime feature-table summarize \
            --i-table {input.table} \
            --m-sample-metadata-file {input.metadata} \
            --o-visualization {output.summary} \
            > {log} 2>&1
        """