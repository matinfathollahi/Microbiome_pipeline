rule taxonomy_batch:

    input:
        repseq=
            "results/qiime2/dada2/batches/{batch}/representative_sequences.qza",

        classifier=
            config["taxonomy"]["classifier"]

    output:
        taxonomy=
            "results/qiime2/taxonomy/batches/{batch}/taxonomy.qza"

    params:
        reads_per_batch=
            config["taxonomy"]["reads_per_batch"],

        confidence=
            config["taxonomy"]["confidence"]

    threads:
        config["taxonomy"]["n_jobs"]

    conda:
        "envs/qiime2.yaml"

    log:
        "logs/qiime2/taxonomy/{batch}.log"

    shell:
        r"""
        mkdir -p $(dirname {output.taxonomy})
        mkdir -p $(dirname {log})

        bash scripts/bash/taxonomy.sh \
            {input.repseq} \
            {input.classifier} \
            {output.taxonomy} \
            {threads} \
            {params.reads_per_batch} \
            {params.confidence} \
            > {log} 2>&1
        """