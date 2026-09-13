rule validate_fastq:
    input:
        r1="data/raw/{accession}_1.fastq.gz",
        r2="data/raw/{accession}_2.fastq.gz"

    output:
        ok="results/validation/{accession}.fastq.ok"

    log:
        "logs/validate_fastq/{accession}.log"

    benchmark:
        "benchmark/validate_fastq/{accession}.txt"

    conda:
        "envs/seqkit.yaml"

    threads:
        2

    shell:
        """
        python scripts/python/validate_fastq.py \
            {input.r1} \
            {input.r2} \
            {output.ok} \
            > {log} 2>&1
        """