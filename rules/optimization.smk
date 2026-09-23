rule optimize_dada2_parameters:

    input:
        demux="results/qiime2/import/{study}/{batch}/demux.qza",
        metadata="metadata/sample_metadata.tsv"

    output:
        params="results/optimization/{study}/{batch}/best_parameters.json"

    conda:
        "envs/optimization.yaml"

    script:
        "../scripts/optimization/optimizer.py"