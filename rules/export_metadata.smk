rule export_metadata:

    input:
        "metadata/sample_metadata.tsv"

    output:
        "results/export/metadata/sample_metadata.tsv"

    log:
        "logs/export/metadata.log"

    benchmark:
        "benchmark/export/metadata.txt"

    conda:
        "envs/python.yaml"

    shell:
        """
        bash scripts/bash/export_metadata.sh \
            {input} \
            {output} \
            > {log} 2>&1
        """