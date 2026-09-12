rule download_sra:

    input:
        preflight=
            "results/qc/preflight/preflight_validation.json"

    output:
        sra=temp("data/sra/{accession}/{accession}.sra")

    params:
        sra_dir=config["download"]["sra_dir"]

    log:
        "logs/download/{accession}.log"

    benchmark:
        "benchmark/download/{accession}.txt"

    conda:
        "envs/sra.yaml"

    threads:
        config["download"]["threads"]

    shell:
        r"""
        mkdir -p $(dirname {output.sra})
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        bash scripts/bash/download_sra.sh \
            {wildcards.accession} \
            {params.sra_dir} \
            > {log} 2>&1
        """