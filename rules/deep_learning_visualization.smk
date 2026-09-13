rule deep_learning_visualization:
    input:
        features=
            "results/deep_learning/data/train_features.tsv",

        labels=
            "results/deep_learning/data/train_labels.tsv",

        nested=
            "results/deep_learning/nested_cv/nested_summary.json",

        artifacts=
            "results/deep_learning/nested_cv/fold_artifacts.tar.gz"

    output:
        summary=
            "results/deep_learning/visualization/visualization_summary.json",

        status=
            "results/deep_learning/visualization/visualization_status.tsv"

    params:
        outdir=
            "results/deep_learning/visualization",

        

        seed=
            config[
                "deep_learning"
            ][
                "random_seed"
            ],

        perplexity=
            config[
                "deep_learning"
            ][
                "visualization"
            ][
                "tsne_perplexity"
            ],

        iterations=
            config[
                "deep_learning"
            ][
                "visualization"
            ][
                "tsne_iterations"
            ],

        neighbors=
            config[
                "deep_learning"
            ][
                "visualization"
            ][
                "umap_neighbors"
            ],

        min_dist=
            config[
                "deep_learning"
            ][
                "visualization"
            ][
                "umap_min_dist"
            ]

    log:
        "logs/deep_learning/visualization.log"

    benchmark:
        "benchmark/deep_learning/visualization.txt"

    conda:
        "envs/deep_learning.yaml"

    shell:
        r"""
        mkdir -p {params.outdir}
        mkdir -p $(dirname {log})

        set -euo pipefail

        MODELS_DIR="$(mktemp -d)"

        trap 'rm -rf "$MODELS_DIR"' EXIT

        tar -tzf {input.artifacts} > /dev/null

        tar -xzf \
            {input.artifacts} \
            -C "$MODELS_DIR"

        PYTHONPATH=scripts/python \
        python -m deep_learning.visualization.run_visualization \
            --features {input.features} \
            --labels {input.labels} \
            --models-dir "$MODELS_DIR" \
            --output {params.outdir} \
            --seed {params.seed} \
            --tsne-perplexity {params.perplexity} \
            --tsne-iterations {params.iterations} \
            --umap-neighbors {params.neighbors} \
            --umap-min-dist {params.min_dist} \
            > {log} 2>&1

        test -s {output.summary}
        test -s {output.status}
        """