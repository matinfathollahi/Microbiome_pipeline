from pathlib import Path
import pandas as pd


def load_accession_table():

    path = Path(
        "metadata/accessions.tsv"
    )

    if not path.is_file():
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            path,
            sep="\t",
            dtype=str
        )

    except Exception:

        return pd.DataFrame()

    return df


ACCESSION_TABLE = load_accession_table()


if (
    not ACCESSION_TABLE.empty
    and
    "DenoiseBatch" in ACCESSION_TABLE.columns
):

    DENOISE_BATCHES = sorted(
        ACCESSION_TABLE[
            "DenoiseBatch"
        ]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

else:

    DENOISE_BATCHES = []


def validated_fastq_for_batch(wildcards):

    if ACCESSION_TABLE.empty:
        return []

    subset = ACCESSION_TABLE[
        ACCESSION_TABLE["DenoiseBatch"]
        .astype(str)
        .str.strip()
        ==
        wildcards.batch
    ]

    accessions = (
        subset["accession"]
        .astype(str)
        .str.strip()
        .tolist()
    )

    return [
        f"results/validation/{acc}.fastq.ok"
        for acc in accessions
    ]


rule generate_manifest:

    input:

        preflight=
            "results/qc/preflight/preflight_validation.json",

        validated=
            validated_fastq_for_batch

    output:

        manifest=
            "metadata/manifests/{batch}.csv"

    log:

        "logs/manifest/{batch}.log"

    conda:

        "envs/python.yaml"

    shell:

        r"""
        mkdir -p metadata/manifests
        mkdir -p $(dirname {log})

        set -euo pipefail

        python scripts/python/generate_manifest.py \
            --accessions metadata/accessions.tsv \
            --raw-dir data/raw \
            --batch "{wildcards.batch}" \
            --output {output.manifest} \
            > {log} 2>&1
        """