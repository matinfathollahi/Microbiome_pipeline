rule optimize_dada2_parameters:

    input:
        demux="results/qiime2/import/{batch}/demux.qza",
        metadata="metadata/sample_metadata.tsv"

    output:
        params="results/optimization/{batch}/best_parameters.json",

    conda:
        "envs/optimization.yaml"

    script:
        "../scripts/optimization/optimizer.py"