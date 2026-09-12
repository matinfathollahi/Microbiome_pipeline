rule taxonomy:

    input:
        repseq="results/qiime2/dada2/representative_sequences.qza",
        classifier=config["taxonomy"]["classifier"]

    output:
        taxonomy="results/qiime2/taxonomy/taxonomy.qza"

    params:
        reads_per_batch=config["taxonomy"]["reads_per_batch"],
        confidence=config["taxonomy"]["confidence"]

    log:
        "logs/qiime2/taxonomy.log"

    benchmark:
        "benchmark/qiime2/taxonomy.txt"

    conda:
        "envs/qiime2.yaml"

    threads:
        config["taxonomy"]["n_jobs"]

    shell:
        """
        bash scripts/bash/taxonomy.sh \
            {input.repseq} \
            {input.classifier} \
            {output.taxonomy} \
            {threads} \
            {params.reads_per_batch} \
            {params.confidence} \
            > {log} 2>&1
        """