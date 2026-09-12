rule validate_sra:

    input:
        sra="data/sra/{accession}/{accession}.sra"

    output:
        ok="results/validation/{accession}.ok"

    log:
        "logs/validate_sra/{accession}.log"

    benchmark:
        "benchmark/validate_sra/{accession}.txt"

    conda:
        "envs/sra.yaml"

    threads:
        1

    shell:
        """
        python scripts/python/validate_sra.py \
            {input.sra} \
            {output.ok} \
            > {log} 2>&1
        """