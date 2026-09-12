rule qiime2_import:

    input:

        manifest=
            "metadata/manifests/{batch}.csv"

    output:

        qza=
            "results/qiime2/import/{batch}/demux.qza"

    log:

        "logs/qiime2/import/{batch}.log"

    benchmark:

        "benchmark/qiime2/import/{batch}.txt"

    conda:

        "envs/qiime2.yaml"

    shell:

        r"""
        mkdir -p $(dirname {output.qza})
        mkdir -p $(dirname {log})
        mkdir -p $(dirname {benchmark})

        set -euo pipefail

        qiime tools import \
            --type 'SampleData[PairedEndSequencesWithQuality]' \
            --input-path {input.manifest} \
            --output-path {output.qza} \
            --input-format PairedEndFastqManifestPhred33V2 \
            > {log} 2>&1
        """