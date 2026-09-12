rule phylogeny:

    input:
        repseq="results/qiime2/dada2/representative_sequences.qza"

    output:

        aligned="results/qiime2/phylogeny/aligned_rep_seqs.qza",

        masked="results/qiime2/phylogeny/masked_aligned_rep_seqs.qza",

        tree="results/qiime2/phylogeny/unrooted_tree.qza",

        rooted="results/qiime2/phylogeny/rooted_tree.qza"

    log:
        "logs/qiime2/phylogeny.log"

    benchmark:
        "benchmark/qiime2/phylogeny.txt"

    conda:
        "envs/qiime2.yaml"

    threads:
        config["phylogeny"]["threads"]

    shell:
        """
        bash scripts/bash/phylogeny.sh \
            {input.repseq} \
            {output.aligned} \
            {output.masked} \
            {output.tree} \
            {output.rooted} \
            > {log} 2>&1
        """