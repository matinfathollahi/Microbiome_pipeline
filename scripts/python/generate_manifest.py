#!/usr/bin/env python3

from pathlib import Path
import argparse
import pandas as pd


# -----------------------------
# Arguments
# -----------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    "--accessions",
    required=True
)

parser.add_argument(
    "--raw-dir",
    required=True
)

parser.add_argument(
    "--output",
    required=True
)

parser.add_argument(
    "--batch",
    required=True
)

args = parser.parse_args()


accessions_file = Path(args.accessions)
raw_dir = Path(args.raw_dir)
output_file = Path(args.output)


# -----------------------------
# Check input files/directories
# -----------------------------

if not accessions_file.is_file():
    raise FileNotFoundError(
        f"Accessions file not found: {accessions_file}"
    )

if not raw_dir.is_dir():
    raise FileNotFoundError(
        f"Raw FASTQ directory not found: {raw_dir}"
    )


# -----------------------------
# Read accession table
# -----------------------------

samples = pd.read_csv(
    accessions_file,
    sep="\t",
    dtype=str
)


# Clean column names
samples.columns = [
    str(column).strip()
    for column in samples.columns
]


# -----------------------------
# Validate required columns
# -----------------------------

required_columns = {
    "SampleID",
    "accession",
    "DenoiseBatch"
}

missing_columns = (
    required_columns
    - set(samples.columns)
)

if missing_columns:
    raise ValueError(
        "metadata/accessions.tsv is missing required columns: "
        + ", ".join(sorted(missing_columns))
    )


# Keep only required columns
samples = samples[
    [
        "SampleID",
        "accession",
        "DenoiseBatch"
    ]
].copy()


# -----------------------------
# Check missing values
# -----------------------------

if samples["SampleID"].isna().any():
    raise ValueError(
        "Missing SampleID values found in accessions.tsv."
    )

if samples["accession"].isna().any():
    raise ValueError(
        "Missing accession values found in accessions.tsv."
    )


# -----------------------------
# Clean values
# -----------------------------

samples["SampleID"] = (
    samples["SampleID"]
    .astype(str)
    .str.strip()
)

samples["accession"] = (
    samples["accession"]
    .astype(str)
    .str.strip()
)



samples["DenoiseBatch"] = (
    samples["DenoiseBatch"]
    .astype(str)
    .str.strip()
)

samples = samples[
    samples["DenoiseBatch"] == args.batch
].copy()

if samples.empty:
    raise ValueError(
        f"No samples found for DenoiseBatch={args.batch}"
    )

# -----------------------------
# Check blank values
# -----------------------------

if samples["SampleID"].eq("").any():
    raise ValueError(
        "Blank SampleID values found in accessions.tsv."
    )

if samples["accession"].eq("").any():
    raise ValueError(
        "Blank accession values found in accessions.tsv."
    )


# -----------------------------
# Check duplicates
# -----------------------------

if samples["SampleID"].duplicated().any():

    duplicates = (
        samples.loc[
            samples["SampleID"].duplicated(
                keep=False
            ),
            "SampleID"
        ]
        .unique()
        .tolist()
    )

    raise ValueError(
        "Duplicate SampleID values found: "
        + ", ".join(duplicates[:10])
    )


if samples["accession"].duplicated().any():

    duplicates = (
        samples.loc[
            samples["accession"].duplicated(
                keep=False
            ),
            "accession"
        ]
        .unique()
        .tolist()
    )

    raise ValueError(
        "Duplicate accession values found: "
        + ", ".join(duplicates[:10])
    )


# -----------------------------
# Build QIIME2 manifest
# -----------------------------

rows = []


for _, sample in samples.iterrows():

    sample_id = sample["SampleID"]
    accession = sample["accession"]

    r1 = (
        raw_dir
        / f"{accession}_1.fastq.gz"
    )

    r2 = (
        raw_dir
        / f"{accession}_2.fastq.gz"
    )


    # Check FASTQ files

    if not r1.is_file():
        raise FileNotFoundError(
            f"Forward FASTQ not found "
            f"for SampleID={sample_id}, "
            f"accession={accession}: {r1}"
        )

    if not r2.is_file():
        raise FileNotFoundError(
            f"Reverse FASTQ not found "
            f"for SampleID={sample_id}, "
            f"accession={accession}: {r2}"
        )


    # Forward read

    rows.append({
        "sample-id": sample_id,
        "absolute-filepath": str(
            r1.resolve()
        ),
        "direction": "forward"
    })


    # Reverse read

    rows.append({
        "sample-id": sample_id,
        "absolute-filepath": str(
            r2.resolve()
        ),
        "direction": "reverse"
    })


# -----------------------------
# Create manifest
# -----------------------------

manifest = pd.DataFrame(
    rows,
    columns=[
        "sample-id",
        "absolute-filepath",
        "direction"
    ]
)


# -----------------------------
# Save manifest
# -----------------------------

output_file.parent.mkdir(
    parents=True,
    exist_ok=True
)

manifest.to_csv(
    output_file,
    index=False
)


# -----------------------------
# Summary
# -----------------------------

print(
    f"Manifest created successfully: "
    f"{output_file}"
)

print(
    f"Samples: {len(samples)}"
)

print(
    f"Manifest rows: {len(manifest)}"
)