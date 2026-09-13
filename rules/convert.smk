rule convert_fastq:
    input:
        sra="data/sra/{accession}/{accession}.sra",
        validation="results/validation/{accession}.sra.ok"

    output:
        r1=temp("data/raw/{accession}_1.fastq"),
        r2=temp("data/raw/{accession}_2.fastq")

    params:
        outdir=config["convert"]["outdir"],
        tempdir=config["convert"]["tempdir"]

    log:
        "logs/convert/{accession}.log"

    benchmark:
        "benchmark/convert/{accession}.txt"

    conda:
        "envs/sra.yaml"

    threads:
        config["convert"]["threads"]

    shell:
        r"""
        mkdir -p $(dirname {output.r1})
        mkdir -p $(dirname {log})

        set -euo pipefail

        bash scripts/bash/convert_fastq.sh \
            {input.sra} \
            {params.outdir} \
            {threads} \
            {params.tempdir} \
            > {log} 2>&1
        """