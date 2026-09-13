rule export_sequences:
    input:
        "results/qiime2/dada2/representative_sequences.qza"

    output:
        directory("results/export/sequences")

    log:
        "logs/export/sequences.log"

    benchmark:
        "benchmark/export/sequences.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        bash scripts/bash/export_sequences.sh \
            {input} \
            {output} \
            > {log} 2>&1
        """