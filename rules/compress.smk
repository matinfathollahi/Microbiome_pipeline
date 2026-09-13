rule compress_fastq:
    input:
        r1="data/raw/{accession}_1.fastq",
        r2="data/raw/{accession}_2.fastq"

    output:
        r1="data/raw/{accession}_1.fastq.gz",
        r2="data/raw/{accession}_2.fastq.gz"

    log:
        "logs/compress/{accession}.log"

    benchmark:
        "benchmark/compress/{accession}.txt"

    conda:
        "envs/compress.yaml"

    threads:
        config["compress"]["threads"]

    shell:
        """
        bash scripts/bash/compress_fastq.sh \
            {input.r1} \
            {input.r2} \
            {threads} \
            > {log} 2>&1
        """