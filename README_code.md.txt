

########################
pip install snakefmt
snakefmt rules/
#####################




# MicrobiomePipeline README

## Installation and Execution Guide

### 1. System Requirements

Recommended: - Ubuntu 22.04 LTS - RAM: 16 GB minimum, 32 GB
recommended - CPU: 8 cores or more - Sufficient storage for databases
and results

------------------------------------------------------------------------

## 2. Install Dependencies

``` bash
sudo apt update
sudo apt install -y wget curl git unzip build-essential python3 python3-pip
```

------------------------------------------------------------------------

## 3. Install Micromamba

``` bash
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)
```

Reload:

``` bash
source ~/.bashrc
```

Check:

``` bash
micromamba --version
```

------------------------------------------------------------------------

## 4. Initialize Micromamba

``` bash
micromamba shell init -s bash
source ~/.bashrc
```

------------------------------------------------------------------------

## 5. Install Snakemake

``` bash
micromamba create -n snakemake -c conda-forge -c bioconda snakemake
```

Activate:

``` bash
micromamba activate snakemake
```

Check:

``` bash
snakemake --version
```

------------------------------------------------------------------------

## 6. Get Pipeline

``` bash
git clone <PROJECT_URL>
cd MicrobiomePipeline
```

Expected:

    Snakefile
    config/
    envs/
    rules/
    scripts/
    data/
    metadata/
    results/

------------------------------------------------------------------------

## 7. Configure

Edit:

    config/config.yaml

Set: - input paths - metadata - study column - groups - database paths -
ML/DL settings - batch correction settings

------------------------------------------------------------------------

## 8. Validate Before Run

``` bash
snakemake --use-conda --conda-frontend mamba --cores 1 -n
```

------------------------------------------------------------------------

## 9. Run Pipeline

Full:

``` bash
snakemake --use-conda --conda-frontend mamba --cores all
```

Resume:

``` bash
snakemake --use-conda --conda-frontend mamba --cores all --rerun-incomplete
```

------------------------------------------------------------------------

## 10. Output Structure

    results/
    ├── qc/
    ├── taxonomy/
    ├── diversity/
    ├── differential_abundance/
    ├── meta_analysis/
    ├── machine_learning/
    ├── deep_learning/
    ├── batch_correction/
    └── publication_bundle/

------------------------------------------------------------------------

## 11. Scientific Analysis Design

Primary:

    Raw ML
    Raw DL

Sensitivity:

    MMUPHin Corrected ML
    MMUPHin Corrected DL

Corrected analyses are interpreted as transductive sensitivity analyses.

------------------------------------------------------------------------

## 12. Reproducibility Report

``` bash
snakemake --report pipeline_report.html
```

------------------------------------------------------------------------

## 13. Useful Commands

List environments:

``` bash
micromamba env list
```

Remove environment:

``` bash
micromamba remove -n snakemake --all
```

Clean cache:

``` bash
micromamba clean --all
```



