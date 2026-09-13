rule export_tree:
    input:
        tree="results/qiime2/phylogeny/rooted_tree.qza"

    output:
        directory("results/export/tree")

    log:
        "logs/export/tree.log"

    benchmark:
        "benchmark/export/tree.txt"

    conda:
        "envs/qiime2.yaml"

    shell:
        r"""
        mkdir -p {output}
        mkdir -p $(dirname {log})

        set -euo pipefail

        bash scripts/bash/export_tree.sh \
            {input.tree} \
            {output} \
            > {log} 2>&1
        """