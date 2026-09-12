rule representative_sequences_summary:

    input:
        repseq="results/qiime2/dada2/representative_sequences.qza"

    output:
        summary="results/qiime2/representative_sequences/representative_sequences.qzv"

    log:
        "logs/qiime2/representative_sequences_summary.log"

    benchmark:
        "benchmark/qiime2/representative_sequences_summary.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        """
        bash scripts/bash/representative_sequences_summary.sh \
            {input.repseq} \
            {output.summary} \
            > {log} 2>&1
        """