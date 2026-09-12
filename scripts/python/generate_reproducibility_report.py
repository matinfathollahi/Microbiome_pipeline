#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


############################################################
# Helpers
############################################################

def run_command(command):

    try:

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        text = (
            result.stdout.strip()
            or result.stderr.strip()
        )

        if result.returncode != 0:

            return "NOT_AVAILABLE"

        return text if text else "UNKNOWN"

    except Exception:

        return "NOT_AVAILABLE"


############################################################

def sha256_file(path):

    path = Path(path)

    digest = hashlib.sha256()

    with open(
        path,
        "rb"
    ) as handle:

        while True:

            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


############################################################

def write_tsv(
    rows,
    columns,
    path
):

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as handle:

        handle.write(
            "\t".join(columns)
            + "\n"
        )

        for row in rows:

            values = [

                str(
                    row.get(
                        column,
                        ""
                    )
                ).replace(
                    "\t",
                    " "
                ).replace(
                    "\n",
                    " "
                )

                for column in columns
            ]

            handle.write(
                "\t".join(values)
                + "\n"
            )


############################################################
# Seeds
############################################################

def collect_seeds(
    obj,
    prefix=""
):

    rows = []

    if isinstance(
        obj,
        dict
    ):

        for key, value in obj.items():

            path = (
                f"{prefix}.{key}"
                if prefix
                else str(key)
            )

            key_lower = str(
                key
            ).lower()

            if (
                "seed" in key_lower
                and
                not isinstance(
                    value,
                    (dict, list)
                )
            ):

                rows.append(
                    {
                        "ConfigPath": path,
                        "Value": value
                    }
                )

            rows.extend(
                collect_seeds(
                    value,
                    path
                )
            )

    elif isinstance(
        obj,
        list
    ):

        for i, value in enumerate(
            obj
        ):

            rows.extend(
                collect_seeds(
                    value,
                    f"{prefix}[{i}]"
                )
            )

    return rows


############################################################
# Conda environments created by Snakemake
############################################################

def collect_conda_packages(
    snakemake_conda_dir
):

    rows = []

    root = Path(
        snakemake_conda_dir
    )

    if not root.exists():

        return rows

    for env_dir in sorted(
        root.iterdir()
    ):

        if not env_dir.is_dir():
            continue

        conda_meta = (
            env_dir
            / "conda-meta"
        )

        if not conda_meta.is_dir():
            continue

        package_files = sorted(
            conda_meta.glob(
                "*.json"
            )
        )

        for package_file in package_files:

            try:

                with open(
                    package_file,
                    "r",
                    encoding="utf-8"
                ) as handle:

                    package = json.load(
                        handle
                    )

                rows.append(
                    {
                        "Environment":
                            env_dir.name,

                        "EnvironmentPath":
                            str(
                                env_dir
                            ),

                        "Package":
                            package.get(
                                "name",
                                ""
                            ),

                        "Version":
                            package.get(
                                "version",
                                ""
                            ),

                        "Build":
                            package.get(
                                "build",
                                ""
                            ),

                        "Channel":
                            package.get(
                                "channel",
                                ""
                            )
                    }
                )

            except Exception:

                continue

    return rows


############################################################
# Workflow checksums
############################################################

def collect_workflow_files(
    project_root
):

    project_root = Path(
        project_root
    )

    files = []

    important_files = [

        project_root / "Snakefile",

        project_root
        / "config"
        / "config.yaml"
    ]

    for file in important_files:

        if file.is_file():

            files.append(
                file
            )

    scan_directories = [

        project_root / "rules",

        project_root / "scripts",

        project_root / "envs"
    ]

    allowed_suffixes = {

        ".smk",
        ".py",
        ".R",
        ".r",
        ".sh",
        ".yaml",
        ".yml"
    }

    for directory in scan_directories:

        if not directory.exists():
            continue

        for path in directory.rglob(
            "*"
        ):

            if (
                path.is_file()
                and
                path.suffix
                in allowed_suffixes
            ):

                files.append(
                    path
                )

    unique_files = sorted(
        set(files)
    )

    rows = []

    for path in unique_files:

        try:

            relative = path.relative_to(
                project_root
            )

        except ValueError:

            relative = path

        rows.append(
            {
                "File":
                    str(
                        relative
                    ),

                "SHA256":
                    sha256_file(
                        path
                    ),

                "Bytes":
                    path.stat().st_size
            }
        )

    return rows


############################################################
# Input checksums
############################################################

def collect_input_checksums(
    paths,
    project_root
):

    rows = []

    project_root = Path(
        project_root
    )

    for input_path in paths:

        path = Path(
            input_path
        )

        if not path.is_file():
            continue

        try:

            display_path = path.relative_to(
                project_root
            )

        except ValueError:

            display_path = path

        rows.append(
            {
                "File":
                    str(
                        display_path
                    ),

                "SHA256":
                    sha256_file(
                        path
                    ),

                "Bytes":
                    path.stat().st_size
            }
        )

    return rows


############################################################
# Git
############################################################

def collect_git_info(
    project_root
):

    project_root = str(
        project_root
    )

    commit = run_command(
        [
            "git",
            "-C",
            project_root,
            "rev-parse",
            "HEAD"
        ]
    )

    branch = run_command(
        [
            "git",
            "-C",
            project_root,
            "rev-parse",
            "--abbrev-ref",
            "HEAD"
        ]
    )

    status = run_command(
        [
            "git",
            "-C",
            project_root,
            "status",
            "--porcelain"
        ]
    )

    if status == "NOT_AVAILABLE":

        dirty = "NOT_AVAILABLE"

    elif status:

        dirty = "YES"

    else:

        dirty = "NO"

    return [
        {
            "Item": "Commit",
            "Value": commit
        },
        {
            "Item": "Branch",
            "Value": branch
        },
        {
            "Item": "WorkingTreeDirty",
            "Value": dirty
        }
    ]


############################################################
# Main
############################################################

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--project-root",
        default="."
    )

    parser.add_argument(
        "--config",
        required=True
    )

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--accessions",
        required=True
    )

    parser.add_argument(
        "--classifier",
        required=True
    )

    parser.add_argument(
        "--publication-summary",
        required=True
    )

    parser.add_argument(
        "--preflight-report",
        required=True
    )

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    project_root = Path(
        args.project_root
    ).resolve()

    output_dir = Path(
        args.output
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    ########################################################
    # Config
    ########################################################

    with open(
        args.config,
        "r",
        encoding="utf-8"
    ) as handle:

        config = yaml.safe_load(
            handle
        )

    if not isinstance(
        config,
        dict
    ):

        raise ValueError(
            "Invalid config YAML."
        )


    ########################################################
    # Freeze exact config used
    ########################################################

    shutil.copy2(

        args.config,

        output_dir
        / "config_used.yaml"
    )


    ########################################################
    # Software versions
    ########################################################

    software_rows = [

        {
            "Software":
                "Python",

            "Version":
                sys.version.replace(
                    "\n",
                    " "
                )
        },

        {
            "Software":
                "Snakemake",

            "Version":
                run_command(
                    [
                        "snakemake",
                        "--version"
                    ]
                )
        },

        {
            "Software":
                "Conda",

            "Version":
                run_command(
                    [
                        "conda",
                        "--version"
                    ]
                )
        },

        {
            "Software":
                "R",

            "Version":
                run_command(
                    [
                        "Rscript",
                        "--version"
                    ]
                )
        },

        {
            "Software":
                "QIIME2",

            "Version":
                run_command(
                    [
                        "qiime",
                        "--version"
                    ]
                )
        },

        {
            "Software":
                "Git",

            "Version":
                run_command(
                    [
                        "git",
                        "--version"
                    ]
                )
        },

        {
            "Software":
                "OperatingSystem",

            "Version":
                platform.platform()
        },

        {
            "Software":
                "Architecture",

            "Version":
                platform.machine()
        },

        {
            "Software":
                "Processor",

            "Version":
                platform.processor()
                or "UNKNOWN"
        }
    ]


    write_tsv(

        software_rows,

        [
            "Software",
            "Version"
        ],

        output_dir
        / "software_versions.tsv"
    )


    ########################################################
    # Seeds
    ########################################################

    seed_rows = collect_seeds(
        config
    )

    write_tsv(

        seed_rows,

        [
            "ConfigPath",
            "Value"
        ],

        output_dir
        / "random_seeds.tsv"
    )


    ########################################################
    # Input hashes
    ########################################################

    input_rows = collect_input_checksums(

        [
            args.config,
            args.metadata,
            args.accessions,
            args.classifier
        ],

        project_root
    )


    write_tsv(

        input_rows,

        [
            "File",
            "SHA256",
            "Bytes"
        ],

        output_dir
        / "input_checksums.tsv"
    )


    ########################################################
    # Workflow source hashes
    ########################################################

    workflow_rows = collect_workflow_files(
        project_root
    )


    write_tsv(

        workflow_rows,

        [
            "File",
            "SHA256",
            "Bytes"
        ],

        output_dir
        / "workflow_checksums.tsv"
    )


    ########################################################
    # Exact packages from Snakemake-created conda envs
    ########################################################

    conda_rows = collect_conda_packages(

        project_root
        / ".snakemake"
        / "conda"
    )


    write_tsv(

        conda_rows,

        [
            "Environment",
            "EnvironmentPath",
            "Package",
            "Version",
            "Build",
            "Channel"
        ],

        output_dir
        / "conda_packages.tsv"
    )


    ########################################################
    # Git
    ########################################################

    git_rows = collect_git_info(
        project_root
    )


    write_tsv(

        git_rows,

        [
            "Item",
            "Value"
        ],

        output_dir
        / "git_info.tsv"
    )


    ########################################################
    # Read final pipeline status files
    ########################################################

    with open(
        args.preflight_report,
        "r",
        encoding="utf-8"
    ) as handle:

        preflight = json.load(
            handle
        )


    with open(
        args.publication_summary,
        "r",
        encoding="utf-8"
    ) as handle:

        publication = json.load(
            handle
        )


    ########################################################
    # Master summary
    ########################################################

    summary = {

        "generated_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "project_root":
            str(
                project_root
            ),

        "preflight_status":
            preflight.get(
                "status",
                "UNKNOWN"
            ),

        "publication_summary":
            publication,

        "workflow_files_hashed":
            len(
                workflow_rows
            ),

        "input_files_hashed":
            len(
                input_rows
            ),

        "conda_packages_recorded":
            len(
                conda_rows
            ),

        "random_seeds_recorded":
            len(
                seed_rows
            ),

        "python_version":
            platform.python_version(),

        "platform":
            platform.platform(),

        "reproducibility_files": [

            "config_used.yaml",
            "software_versions.tsv",
            "conda_packages.tsv",
            "random_seeds.tsv",
            "input_checksums.tsv",
            "workflow_checksums.tsv",
            "git_info.tsv"
        ],

        "notes": [

            (
                "SHA256 hashes uniquely identify "
                "the checked input/workflow files."
            ),

            (
                "Conda package versions are collected "
                "directly from Snakemake-created "
                ".snakemake/conda environments."
            ),

            (
                "NOT_AVAILABLE means a command was not "
                "visible inside the reporting environment; "
                "resolved packages may still be recorded "
                "from conda-meta."
            )
        ]
    }


    with open(

        output_dir
        / "reproducibility_summary.json",

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(
            summary,
            handle,
            indent=2
        )


    print()
    print(
        "Reproducibility report completed."
    )
    print(
        f"Workflow files hashed : {len(workflow_rows)}"
    )
    print(
        f"Input files hashed    : {len(input_rows)}"
    )
    print(
        f"Conda packages        : {len(conda_rows)}"
    )
    print(
        f"Random seeds          : {len(seed_rows)}"
    )
    print()


if __name__ == "__main__":

    main()