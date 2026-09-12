rule export_taxonomy:

    input:
        taxonomy="results/qiime2/taxonomy/taxonomy.qza"

    output:
        taxonomy="results/export/taxonomy/taxonomy.tsv"

    params:
        outdir="results/export/taxonomy"

    log:
        "logs/export/taxonomy.log"

    benchmark:
        "benchmark/export/taxonomy.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        mkdir -p {params.outdir}

        qiime tools export \
            --input-path {input.taxonomy} \
            --output-path {params.outdir} \
            > {log} 2>&1

        test -f {output.taxonomy}
        """