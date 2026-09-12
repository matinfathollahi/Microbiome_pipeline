# Microbiome Meta-Analysis Pipeline

A Snakemake-based, multi-study 16S rRNA microbiome workflow integrating QIIME 2, R, Python, classical machine learning, deep learning, study-aware validation, batch-effect diagnostics/correction, differential abundance, meta-analysis, and publication/reproducibility outputs.

This README corresponds to the reviewed archive:

`MicrobiomePipeline(20260819-052848).zip`

---

## 1. Current input policy

### Required metadata for the current configuration

The current workflow requires the following columns for a complete run:

- `SampleID`
- `Study`
- `Group`
- `Age`
- `Sex`

`SampleID`, `Study`, and `Group` are the core identifiers used throughout the pipeline.

`Age` and `Sex` are currently included in:

```yaml
machine_learning:
  metadata_columns:
    - SampleID
    - Group
    - Study
    - Age
    - Sex
```

Therefore, with the current configuration, `Age` and `Sex` should be present in `metadata/sample_metadata.tsv` for the full ML workflow.

### BMI and Smoking

**BMI and Smoking are NOT required in the current version.**

They have been removed from the active ML/confounding configuration and their absence will not stop the active pipeline.

The only remaining BMI reference is in an old Python ML preparation script used by a `.disabled` rule, so it is not part of the current execution path.

### Batch and Center

`Batch` and `Center` may be supplied when available, but they are not core requirements for the current run.

The current batch-correction configuration is:

```yaml
batch_correction:
  enabled: true
  method: mmuphin
  batch_variable: Study
  biological_variable: Group
```

Therefore, `Study` is currently the batch/harmonization variable used by the correction branch.

Some variance-partition/confounding diagnostics also list `Batch` or `Center`. Their R scripts skip unavailable variables rather than failing solely because one of those optional variables is absent.

---

## 2. Required files

Before starting the workflow, provide these files:

```text
metadata/sample_metadata.tsv
metadata/accessions.tsv
database/silva-138-99-classifier.qza
```

The pipeline currently expects **paired-end sequencing data**.

---

## 3. `sample_metadata.tsv` format

The metadata file must be a tab-separated TSV file.

Recommended format for the current configuration:

```tsv
SampleID	Study	Group	Age	Sex	Batch	Center
S001	StudyA	Control	34	Female	Run1	CenterA
S002	StudyA	Disease	51	Male	Run1	CenterA
S003	StudyA	Control	40	Female	Run1	CenterA
S004	StudyA	Disease	46	Male	Run1	CenterA
S005	StudyA	Control	37	Female	Run1	CenterA
S006	StudyA	Disease	55	Female	Run1	CenterA
S007	StudyA	Control	31	Male	Run1	CenterA
S008	StudyA	Disease	49	Female	Run1	CenterA
S009	StudyA	Control	43	Male	Run1	CenterA
S010	StudyA	Disease	52	Male	Run1	CenterA
```

A minimal current-format metadata file can therefore be:

```tsv
SampleID	Study	Group	Age	Sex
S001	StudyA	Control	34	Female
S002	StudyA	Disease	51	Male
S003	StudyB	Control	39	Female
S004	StudyB	Disease	48	Male
```

Do **not** add fake BMI or Smoking values simply to fill missing metadata. If those variables were not reported in the original study, leave them out of the dataset.

### Current class labels

The default configuration uses:

```text
Control
Disease
```

because:

```yaml
meta_analysis:
  reference_group: Control
  case_group: Disease
```

If your biological groups have different names, update the corresponding configuration values consistently before running the pipeline.

---

## 4. `accessions.tsv` format

`metadata/accessions.tsv` must contain at least the following columns:

- `SampleID`
- `accession`
- `DenoiseBatch`
- `AmpliconRegion`
- `PrimerSet`

Example:

```tsv
SampleID	accession	DenoiseBatch	AmpliconRegion	PrimerSet
S001	SRR12345601	BatchA	V4	515F-806R
S002	SRR12345602	BatchA	V4	515F-806R
S003	ERR12345603	BatchB	V4	515F-806R
S004	DRR12345604	BatchB	V4	515F-806R
```

### Accession rules

The preflight validator checks that:

- `SampleID` values are not blank.
- `SampleID` values are unique in `accessions.tsv`.
- SRA accessions are unique.
- Standard SRA accessions use `SRR`, `ERR`, or `DRR` prefixes followed by digits.
- Every metadata sample has a corresponding accession.
- Accession SampleIDs occur in the metadata file.
- `DenoiseBatch` is present.
- `AmpliconRegion` is present.
- `PrimerSet` is present.
- All samples use one compatible `AmpliconRegion`/`PrimerSet` combination for ASV-level cross-study merging.

---

## 5. Example multi-study design

Several of the active downstream rules use stricter thresholds than the basic meta-analysis preflight settings.

For example, the current configuration includes:

```yaml
differential_abundance:
  min_samples_per_group: 5
  min_studies: 3

lefse:
  min_samples_per_group: 5
  min_studies: 3

alpha_statistics:
  min_samples_per_group: 5
  min_studies: 3

selbal:
  min_samples_per_group: 5
  min_studies: 3
```

Therefore, a practical minimum design for exercising the complete workflow is:

```text
3 studies
×
(5 Control + 5 Disease per study)
=
30 samples
```

More studies and more samples per study are strongly preferable, especially for study-aware ML/DL validation and meta-analysis.

---

## 6. Example 30-sample metadata structure

```tsv
SampleID	Study	Group	Age	Sex
A_C01	StudyA	Control	32	Female
A_C02	StudyA	Control	41	Male
A_C03	StudyA	Control	38	Female
A_C04	StudyA	Control	45	Male
A_C05	StudyA	Control	36	Female
A_D01	StudyA	Disease	48	Male
A_D02	StudyA	Disease	53	Female
A_D03	StudyA	Disease	46	Male
A_D04	StudyA	Disease	57	Female
A_D05	StudyA	Disease	50	Male
B_C01	StudyB	Control	35	Female
B_C02	StudyB	Control	42	Male
B_C03	StudyB	Control	39	Female
B_C04	StudyB	Control	44	Male
B_C05	StudyB	Control	37	Female
B_D01	StudyB	Disease	49	Male
B_D02	StudyB	Disease	54	Female
B_D03	StudyB	Disease	47	Male
B_D04	StudyB	Disease	56	Female
B_D05	StudyB	Disease	51	Male
C_C01	StudyC	Control	33	Female
C_C02	StudyC	Control	40	Male
C_C03	StudyC	Control	37	Female
C_C04	StudyC	Control	43	Male
C_C05	StudyC	Control	36	Female
C_D01	StudyC	Disease	48	Male
C_D02	StudyC	Disease	52	Female
C_D03	StudyC	Disease	45	Male
C_D04	StudyC	Disease	55	Female
C_D05	StudyC	Disease	50	Male
```

---

## 7. SILVA classifier

Place the QIIME 2 classifier here:

```text
database/silva-138-99-classifier.qza
```

The current config points to:

```yaml
taxonomy:
  classifier: "database/silva-138-99-classifier.qza"
```

The preflight validator checks that the classifier exists, is non-empty, is a valid QZA ZIP archive, and has the expected QIIME artifact structure.

The classifier should also be appropriate for the selected amplicon region and QIIME 2 environment.

---

## 8. Recommended platform

Linux is recommended.

On Windows, use **WSL2** rather than native Windows for the complete Snakemake/Conda/QIIME 2 workflow.

---

## 9. Install the Snakemake runner environment

If Snakemake is not already installed:

```bash
conda create -n microbiome-runner \
  -c conda-forge \
  -c bioconda \
  python=3.11 \
  snakemake

conda activate microbiome-runner
```

The analysis-specific Conda environments are defined under:

```text
envs/
```

and are created automatically by Snakemake when `--use-conda` is used.

---

## 10. Full execution

From the pipeline root directory:

```bash
cd MicrobiomePipeline
```

For 16 CPU cores:

```bash
bash run_pipeline.sh 16
```

For 8 CPU cores:

```bash
bash run_pipeline.sh 8
```

If no core count is supplied, the script defaults to 8 cores.

---

## 11. What `run_pipeline.sh` does

The launcher performs three stages automatically.

### Stage 1 — Preflight validation

Equivalent command:

```bash
snakemake \
  --use-conda \
  --cores 1 \
  --rerun-incomplete \
  --forcerun preflight_validation \
  results/qc/preflight/preflight_validation.json
```

The main preflight output is:

```text
results/qc/preflight/preflight_validation.json
```

Additional preflight checks are written under:

```text
results/qc/preflight/
```

### Stage 2 — DAG dry-run

```bash
snakemake \
  --dry-run \
  --printshellcmds \
  --use-conda \
  --cores 16
```

This checks whether Snakemake can construct the requested DAG before expensive execution begins.

### Stage 3 — Full pipeline

```bash
snakemake \
  --use-conda \
  --cores 16 \
  --rerun-incomplete \
  --printshellcmds
```

The easiest production command remains:

```bash
bash run_pipeline.sh 16
```

---

## 12. Important DADA2 settings

The current config contains:

```yaml
dada2:
  trim_left_f: 17
  trim_left_r: 21
  trunc_len_f: 240
  trunc_len_r: 200
  max_ee_f: 2
  max_ee_r: 2
  trunc_q: 2
  chimera_method: consensus
  pooling: independent
  min_overlap: 20
```

These values should **not** be treated as universally correct for every study.

Before production analysis, verify them against:

- read length,
- primer length,
- forward quality profile,
- reverse quality profile,
- expected amplicon length,
- required paired-end overlap.

The retained forward and reverse sequences must maintain adequate overlap after trimming/truncation.

---

## 13. Rarefaction / sampling depth

The current configuration contains:

```yaml
diversity:
  sampling_depth: 10000
```

After DADA2, inspect the sequencing-depth distribution before accepting this value.

A sampling depth that is too high can discard too many samples. A sampling depth that is too low can waste usable sequencing information.

---

## 14. Main workflow components

The pipeline includes branches for:

- SRA download
- SRA validation
- paired-end FASTQ conversion
- compression
- FASTQ validation
- QIIME 2 manifest generation
- QIIME 2 import
- per-batch DADA2 denoising
- denoising statistics
- taxonomy
- phylogeny
- core diversity
- alpha diversity
- alpha statistics
- beta diversity
- study-aware beta analysis
- PERMANOVA
- study-aware PERMDISP
- feature-table export
- taxonomy export
- abundance/prevalence filtering
- zero replacement
- CLR normalization
- batch-effect correction
- before/after batch diagnostics
- confounding checks
- variance partitioning
- ANCOM-BC2
- ALDEx2
- MaAsLin2
- supplementary DA comparison
- LEfSe
- per-study LEfSe
- Selbal
- per-study differential analysis / meta-analysis
- metafor random-effects meta-analysis
- forest plots
- funnel/publication-bias outputs
- meta-analysis heatmaps
- classical ML
- feature selection
- nested cross-validation
- Optuna hyperparameter optimization
- final model evaluation
- deep learning
- deep-learning nested CV
- deep-learning final evaluation
- deep-learning visualization
- deep-learning explainability
- batch-corrected ML sensitivity analysis
- batch-corrected DL sensitivity analysis
- Raw vs corrected comparison
- publication bundle
- reproducibility bundle

---

## 15. Predictive batch correction — interpretation

The current configuration explicitly defines the batch-corrected predictive branch as:

```yaml
predictive_sensitivity:
  enabled: true
  role: transductive_sensitivity
  primary_analysis: false
  uses_all_samples_for_harmonization: true
```

Therefore:

- Raw ML/DL should be treated as the **primary predictive analysis**.
- Batch-corrected ML/DL should be presented as a **transductive sensitivity analysis**.
- Corrected predictive performance should not be interpreted as a strict inductive estimate for a completely unseen external cohort.

---

## 16. Missing clinical covariates

Public microbiome studies frequently lack harmonized BMI, Smoking, Age, Sex, medication, diet, or center information.

The preferred rule is:

> Do not invent or aggressively impute a clinical covariate merely to make studies look harmonized.

For this reviewed version:

- `BMI`: not required.
- `Smoking`: not required.
- `Age`: currently required by the active ML dataset configuration.
- `Sex`: currently required by the active ML dataset configuration.
- `Batch`: optional as a standalone column in the current configuration because batch correction uses `Study` as `batch_variable`.
- `Center`: optional for diagnostics; unavailable variables can be skipped by the relevant scripts.

If Age or Sex are also unavailable in a future dataset, remove them from `machine_learning.metadata_columns` or update the pipeline so these clinical covariates are explicitly handled as optional before launching the complete workflow.

---

## 17. Main output directories

Important results are written under locations such as:

```text
results/qc/preflight/
results/qiime2/
results/export/
results/ancombc2/
results/aldex2/
results/maaslin2/
results/lefse/
results/selbal/
results/meta_analysis/
results/batch_effect/
results/machine_learning/
results/machine_learning_batch_corrected/
results/deep_learning/
results/publication/
results/reproducibility/
```

Execution logs are stored under:

```text
logs/
```

Benchmarks are stored under:

```text
benchmark/
```

---

## 18. Resume an interrupted run

Snakemake normally resumes incomplete workflows automatically when rerun with:

```bash
bash run_pipeline.sh 16
```

If a stale Snakemake lock remains after an abnormal termination:

```bash
snakemake --unlock
```

Then rerun:

```bash
bash run_pipeline.sh 16
```

---

## 19. Recommended pre-run checklist

Before starting a full analysis, verify:

- [ ] `metadata/sample_metadata.tsv` exists.
- [ ] `metadata/accessions.tsv` exists.
- [ ] SILVA classifier exists.
- [ ] SampleIDs are unique.
- [ ] Accession values are unique.
- [ ] Every metadata SampleID has an accession.
- [ ] Every accession SampleID occurs in metadata.
- [ ] `Study` and `Group` are populated.
- [ ] `Age` and `Sex` are available for the current ML configuration.
- [ ] BMI is not required.
- [ ] Smoking is not required.
- [ ] All samples use a compatible amplicon region and primer set.
- [ ] FASTQ data are paired-end.
- [ ] DADA2 truncation settings match the quality profiles.
- [ ] Forward/reverse reads retain sufficient overlap.
- [ ] `sampling_depth` is reasonable after DADA2.
- [ ] At least three eligible studies exist for the stricter multi-study branches.
- [ ] Preferably at least five Control and five Disease samples are available per study for the complete default DA/LEfSe/alpha/Selbal workflow.
- [ ] Preflight passes.
- [ ] Snakemake dry-run succeeds.

---

## 20. Final command

After preparing the inputs and validating configuration-specific parameters:

```bash
conda activate microbiome-runner
cd MicrobiomePipeline
bash run_pipeline.sh 16
```

This runs:

```text
Preflight validation
        ↓
Snakemake DAG dry-run
        ↓
Complete end-to-end workflow
```

---

## 21. Review status of this archive

Static review of `MicrobiomePipeline(20260819-052848).zip` found:

- `config/config.yaml` parses successfully as YAML.
- All active Snakefile `include:` targets exist.
- Python scripts compile successfully.
- Bash scripts pass shell syntax validation.
- BMI and Smoking are no longer required by the active configuration.
- The old BMI reference is confined to a Python script associated with a disabled rule.
- Current ML metadata columns are `SampleID`, `Group`, `Study`, `Age`, and `Sex`.
- Current batch-correction variable is `Study`.

A true end-to-end biological run still requires the real metadata, SRA accessions/FASTQs, SILVA classifier, compatible Conda environments, and adequate computing resources.
