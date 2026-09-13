# Microbiome Meta-Analysis Pipeline

A Snakemake-based, multi-study 16S rRNA microbiome workflow integrating QIIME 2, R, and Python: amplicon processing (DADA2), diversity analysis, batch-effect diagnostics/correction, differential abundance (ANCOM-BC2 primary; ALDEx2 and MaAsLin2 as supplementary sensitivity checks), LEfSe, Selbal, classical machine learning and deep learning with nested cross-validation, random-effects meta-analysis, and a publication/reproducibility bundle.

**فایل README فارسی در ادامه همین سند، بعد از بخش انگلیسی آمده است.** (See [بخش فارسی](#پایپلاین-متاآنالیز-میکروبیوم-فارسی) below.)

---

## 1. Status of this repository

This pipeline was audited and repaired end-to-end. As of the current commit:

- The full Snakemake DAG (**347 jobs**, from SRA download through the publication bundle) builds successfully with `snakemake -n` (dry-run) — zero errors.
- A systemic parsing incompatibility between this codebase's rule-file formatting style and Snakemake 9.x (a blank line immediately after `rule <name>:`/`checkpoint <name>:` or after section keywords such as `input:`/`output:`) was found and fixed across ~140 locations in `rules/*.smk`.
- Several real DAG wiring bugs were found and fixed: an output-filename collision between `validate_sra` and `validate_fastq`, a broken dependency on a bare directory instead of a specific file (`selbal`, `core_metrics`), and invalid `{benchmark}`/unescaped-brace usage inside `shell:` blocks (42 files).
- `metadata/sample_metadata.tsv` and `metadata/accessions.tsv` now contain **real, usable data**: 45 samples across 3 published studies (PRJEB39064, PRJNA548462, PRJNA1013236) on oral/head-and-neck squamous cell carcinoma vs. healthy control microbiomes, with `Group` normalized to `Control`/`Disease` to match the pipeline's contrast configuration.
- `differential_abundance.enabled` / `.primary_method` and `supplementary_differential_abundance.*.enabled` now really gate which targets `rule all` and the publication bundle request (previously these config keys were documentation-only).
- Beta diversity / PERMANOVA / PERMDISP (study-aware) results are now included in the publication bundle.
- `confounding.batch` is a required, independently-validated metadata column in preflight.
- DADA2 `trim`/`trunc` parameters can now be overridden per `DenoiseBatch` via `dada2.batch_overrides` in the config, falling back to the global values.
- Preflight validation was run for real against the fixed metadata and **passes all checks**.
- One real sample (`ERR4296609`, part of study PRJEB39064) was downloaded live from ENA/SRA to confirm the download stage works against a real accession.

What has **not** been executed in this session: the full 45-sample amplicon processing (DADA2/taxonomy/diversity) and the downstream ML/DL/differential-abundance stages. Those require either the pre-existing `qiime2_env` (repaired — see §9) or fresh per-rule conda environments built by `snakemake --use-conda`, and real compute time (hours, not minutes, especially for nested CV and deep-learning stages). See §11 for exactly how to run them.

---

## 2. Required metadata for the current configuration

The workflow requires the following columns in `metadata/sample_metadata.tsv`:

- `SampleID`, `Study`, `Group` — core identifiers used throughout the pipeline.
- `Age`, `Sex` — used by `machine_learning.metadata_columns`.
- `Batch` — used by `confounding.batch` (independently validated in preflight) and available as the standalone batch column for diagnostics.
- `Center` — used by `variance_partition`/`confounding` diagnostics (optional; scripts skip it if absent).

`BMI` and `Smoking` are **not** required by the active configuration.

### Current class labels

```yaml
meta_analysis:
  reference_group: Control
  case_group: Disease
```

If your biological groups have different names, update the corresponding configuration values consistently (`differential_abundance`, `meta_analysis`, `beta`, `permdisp`, `lefse`, `alpha_statistics`, `selbal`) before running.

---

## 3. Required input files

```text
metadata/sample_metadata.tsv
metadata/accessions.tsv
database/silva-138-99-classifier.qza
```

The pipeline expects **paired-end** sequencing data.

### `sample_metadata.tsv` format

```tsv
SampleID	Study	Group	Age	Sex	Batch	Center
S001	StudyA	Control	34	Female	StudyA	StudyA
S002	StudyA	Disease	51	Male	StudyA	StudyA
```

### `accessions.tsv` format

```tsv
SampleID	accession	DenoiseBatch	AmpliconRegion	PrimerSet
S001	SRR12345601	StudyA	V3-V4	V3-V4
S002	ERR12345602	StudyA	V3-V4	V3-V4
```

Preflight validates: non-blank/unique `SampleID`, unique accessions, standard `SRR`/`ERR`/`DRR` accession format, every metadata sample has a matching accession (and vice versa), `DenoiseBatch`/`AmpliconRegion`/`PrimerSet` present, and a single compatible amplicon region/primer set across all samples (required for cross-study ASV merging).

### Example multi-study design

```yaml
differential_abundance: {min_samples_per_group: 5, min_studies: 3}
lefse:                  {min_samples_per_group: 5, min_studies: 3}
alpha_statistics:       {min_samples_per_group: 5, min_studies: 3}
selbal:                 {min_samples_per_group: 5, min_studies: 3}
```

A practical minimum is **3 studies × (5 Control + 5 Disease) = 30 samples**. The dataset currently in `metadata/` (45 samples, 3 studies) already satisfies this.

---

## 4. SILVA classifier

```text
database/silva-138-99-classifier.qza
```

Preflight checks the file exists, is non-empty, is a valid QZA ZIP archive, and has the expected internal QIIME 2 artifact structure. The classifier must match the amplicon region and the QIIME 2 version in use.

---

## 5. Recommended platform

Linux is recommended. On Windows, use **WSL2**.

---

## 6. Installing the tools

### Snakemake (workflow runner)

```bash
conda create -n microbiome-runner -c conda-forge -c bioconda python=3.11 snakemake
conda activate microbiome-runner
```

Per-rule analysis environments are defined under `rules/envs/*.yaml` and are created automatically by Snakemake when `--use-conda` is passed — no manual installation needed for those.

### QIIME 2 (only if you are not using `--use-conda` for the QIIME 2 rules)

```bash
mamba create -p ./qiime2_env -c https://packages.qiime2.org/qiime2/2026.7/qiime2/released -c conda-forge -c bioconda qiime2=2026.7.0 q2cli=2026.7.0
```

> **If you copy or move a pre-built QIIME 2 conda environment to a new path** (as happened in this repository — the environment was originally built at a different absolute path), every script under its `bin/` (and some binaries under `lib/`, notably `Rscript`) will have the old path hard-coded and will fail with `cannot execute: required file not found` or `No such file or directory`. Fix it by replacing every occurrence of the old absolute path with the new one:
> - For **text** files (scripts with a `#!` shebang): a plain find-and-replace is safe.
> - For **compiled binaries** (ELF executables where the path is embedded as a fixed-length string, e.g. `Rscript`): the replacement string must be padded with trailing `NUL` bytes to preserve the exact original byte length, or the binary will be corrupted. Do **not** use a plain text editor or `sed` on these files.
> There is no `conda-unpack` step available for an environment that wasn't built with `conda-pack`, so this manual path fix is the correct remedy.

---

## 7. Validate before running

```bash
snakemake --use-conda --conda-frontend mamba --cores 1 -n
```

This should report **347 jobs** and exit with status 0 and no errors. If it doesn't, do not proceed to a full run — fix the reported error first.

---

## 8. Full execution

```bash
cd MicrobiomePipeline
bash run_pipeline.sh 16        # or your CPU core count; defaults to 8
```

`run_pipeline.sh` runs three stages automatically:

1. **Preflight validation** — `snakemake --use-conda --cores 1 --forcerun preflight_validation results/qc/preflight/preflight_validation.json`
2. **DAG dry-run** — `snakemake --dry-run --printshellcmds --use-conda --cores <N>`
3. **Full pipeline** — `snakemake --use-conda --cores <N> --rerun-incomplete --printshellcmds`

To resume an interrupted run, just rerun the same command (Snakemake resumes automatically). If a stale lock remains after an abnormal termination: `snakemake --unlock`, then rerun.

---

## 9. Important DADA2 settings

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
  batch_overrides: {}   # per-DenoiseBatch overrides, see below
```

These are **not** universally correct for every study — verify against read length, primer length, and the forward/reverse quality profiles before a production run. If studies differ in read quality, override specific parameters per batch instead of changing the global defaults:

```yaml
dada2:
  batch_overrides:
    PRJEB39064:
      trunc_len_f: 230
      trunc_len_r: 190
```

Any parameter not listed for a batch falls back to the global value.

### Rarefaction / sampling depth

```yaml
diversity:
  sampling_depth: 10000
```

Inspect the sequencing-depth distribution after DADA2 before accepting this value — too high discards samples, too low wastes information.

---

## 10. Main workflow components

SRA download → SRA/FASTQ validation → compression → QIIME 2 import → per-batch DADA2 → denoising stats → taxonomy → phylogeny → core/alpha/beta diversity → PERMANOVA/PERMDISP (study-aware) → feature-table/taxonomy export → filtering → zero replacement → CLR normalization → batch-effect correction (MMUPHin) + before/after diagnostics → confounding checks → variance partitioning → **ANCOM-BC2** (primary DA) → **ALDEx2** + **MaAsLin2** (supplementary DA) → cross-method robustness comparison → LEfSe (pooled + per-study + consensus) → Selbal (LOSO) → per-study effect sizes → `metafor` random-effects meta-analysis → forest/funnel/heatmap outputs → classical ML (Boruta/ElasticNet/RF feature selection → consensus → nested CV → Optuna → final evaluation) → deep learning (nested CV → final evaluation → visualization → explainability) → batch-corrected ML/DL sensitivity analysis → raw-vs-corrected comparison → **publication bundle** → **reproducibility report**.

### Predictive batch correction — interpretation

```yaml
predictive_sensitivity:
  enabled: true
  role: transductive_sensitivity
  primary_analysis: false
```

Raw ML/DL is the **primary** predictive analysis. Batch-corrected ML/DL is a **transductive sensitivity analysis** only — do not interpret it as an inductive estimate for a fully unseen external cohort.

---

## 11. What you still need to do to get real biological results

This audit fixed every structural/wiring bug found and validated the DAG and preflight against real data, but did **not** execute the full 45-sample analysis (that requires hours of compute and, for the R-based rules, conda environments that could not be fully solved in this sandboxed session due to network instability — see below). To get real results:

1. `conda activate microbiome-runner` (or otherwise ensure `snakemake` is on `PATH`).
2. `snakemake --use-conda --cores <N> -n` — confirm it still reports 347 jobs, 0 errors.
3. `bash run_pipeline.sh <N>` — let Snakemake build each rule's conda environment on first use (the R/Bioconductor environments — ANCOM-BC2, ALDEx2, MaAsLin2, DESeq2, sva/MMUPHin — are the slowest to solve; expect this step alone to take a while depending on your network/mirror speed) and then execute the full DAG.
4. Inspect `results/qc/preflight/preflight_checks.tsv`, `results/publication/manifest.tsv`, and `results/reproducibility/reproducibility_summary.json` when it completes.

If you hit conda/mamba `SSL_read` or "could not connect to server" errors while building an environment, that is a network/mirror issue, not a pipeline bug — retry, or point `--conda-frontend`/channel mirrors at a stable network.

---

## 12. Main output directories

```text
results/qc/preflight/        results/qiime2/            results/export/
results/ancombc2/            results/aldex2/            results/maaslin2/
results/lefse/                results/selbal/            results/meta_analysis/
results/batch_effect/        results/machine_learning/  results/machine_learning_batch_corrected/
results/deep_learning/       results/publication/       results/reproducibility/
```

Execution logs: `logs/`. Benchmarks: `benchmark/`.

---

## 13. Pre-run checklist

- [ ] `metadata/sample_metadata.tsv` and `metadata/accessions.tsv` exist and are **plain TSV** (not a spreadsheet saved with a `.tsv` extension — verify with `file metadata/*.tsv`; it must say `ASCII text`, not `Microsoft Excel` / `Zip archive`).
- [ ] SILVA classifier exists at `database/silva-138-99-classifier.qza`.
- [ ] SampleIDs and accessions are unique; every metadata SampleID has a matching accession and vice versa.
- [ ] `Study`, `Group`, `Age`, `Sex`, `Batch` are populated; `Group` values match `reference_group`/`case_group` in the config exactly.
- [ ] All samples share one amplicon region/primer set.
- [ ] FASTQ data are paired-end.
- [ ] DADA2 trim/trunc settings match the quality profiles (use `dada2.batch_overrides` if studies differ).
- [ ] `diversity.sampling_depth` is reasonable after inspecting DADA2 output.
- [ ] At least 3 eligible studies, ideally ≥5 Control + ≥5 Disease samples per study.
- [ ] `snakemake --use-conda --cores 1 -n` succeeds with 0 errors.
- [ ] Preflight passes: `results/qc/preflight/preflight_validation.json` → `"status": "PASS"`.

---

<a id="پایپلاین-متاآنالیز-میکروبیوم-فارسی"></a>
## بخش فارسی

# پایپلاین متاآنالیز میکروبیوم

یک پایپلاین چندمطالعه‌ای مبتنی بر Snakemake برای داده‌های ۱۶S rRNA که QIIME 2، R و Python را برای پردازش آمپلیکون (DADA2)، تحلیل تنوع، تشخیص/تصحیح اثر Batch، فراوانی افتراقی (ANCOM-BC2 به‌عنوان روش اصلی؛ ALDEx2 و MaAsLin2 به‌عنوان تحلیل حساسیت مکمل)، LEfSe، Selbal، یادگیری ماشین کلاسیک و یادگیری عمیق با اعتبارسنجی متقاطع تودرتو، متاآنالیز اثرات تصادفی، و تهیهٔ بستهٔ نهایی مقاله/تکرارپذیری، یکپارچه می‌کند.

---

## ۱. وضعیت فعلی این مخزن

این پایپلاین به‌طور کامل بازبینی و اشکال‌زدایی شد. در کامیت فعلی:

- کل DAG اسنیک‌میک (**۳۴۷ job**، از دانلود SRA تا بستهٔ نهایی مقاله) با `snakemake -n` (اجرای آزمایشی) بدون هیچ خطایی ساخته می‌شود.
- یک ناسازگاری سیستمی بین سبک نگارش فایل‌های rule این پروژه و نسخهٔ ۹ اسنیک‌میک (خط خالی بلافاصله بعد از `rule نام:`/`checkpoint نام:` یا بعد از کلیدواژه‌هایی مثل `input:`/`output:`) در حدود ۱۴۰ نقطه از `rules/*.smk` پیدا و رفع شد.
- چند باگ واقعی دیگر در گراف وابستگی‌ها پیدا و رفع شد: تداخل نام فایل خروجی بین rule های `validate_sra` و `validate_fastq`، وابستگی اشتباه به پوشه به‌جای فایل مشخص (`selbal`، `core_metrics`)، و استفادهٔ نادرست از `{benchmark}`/آکولاد فرارگذاری‌نشده داخل بلوک‌های `shell:` (در ۴۲ فایل).
- فایل‌های `metadata/sample_metadata.tsv` و `metadata/accessions.tsv` اکنون حاوی **دادهٔ واقعی و قابل‌استفاده** هستند: ۴۵ نمونه از ۳ مطالعهٔ منتشرشده (PRJEB39064، PRJNA548462، PRJNA1013236) دربارهٔ میکروبیوم سرطان سلول سنگفرشی دهان/سر و گردن در مقابل افراد سالم، با ستون `Group` نرمال‌شده به `Control`/`Disease` مطابق تنظیمات کنتراست پایپلاین.
- `differential_abundance.enabled`/`.primary_method` و `supplementary_differential_abundance.*.enabled` اکنون واقعاً تعیین‌کنندهٔ اهداف درخواستی `rule all` و بستهٔ مقاله هستند (پیش‌تر این کلیدهای config صرفاً مستندسازی بودند، بدون اثر واقعی روی اجرا).
- نتایج Beta diversity / PERMANOVA / PERMDISP (نسخهٔ مطالعه‌آگاه) اکنون در بستهٔ مقاله گنجانده می‌شوند.
- `confounding.batch` اکنون یک ستون الزامی و مستقلاً اعتبارسنجی‌شده در preflight است.
- پارامترهای `trim`/`trunc` در DADA2 اکنون قابل بازنویسی به‌ازای هر `DenoiseBatch` از طریق `dada2.batch_overrides` در config هستند (با بازگشت به مقادیر سراسری در صورت عدم تعریف).
- اعتبارسنجی preflight به‌صورت واقعی روی دادهٔ تعمیرشده اجرا شد و **تمام بررسی‌ها را با موفقیت رد کرد**.
- یک نمونهٔ واقعی (`ERR4296609`، از مطالعهٔ PRJEB39064) به‌صورت زنده از ENA/SRA دانلود شد تا درستی مرحلهٔ دانلود روی یک accession واقعی تأیید شود.

آنچه در این نشست **اجرا نشد**: پردازش کامل آمپلیکون برای هر ۴۵ نمونه (DADA2/taxonomy/diversity) و مراحل پایین‌دستی ML/DL/فراوانی افتراقی. این مراحل به یکی از این دو نیاز دارند: محیط از‌قبل‌موجود `qiime2_env` (تعمیرشده — بخش ۹ زیر را ببینید) یا محیط‌های conda تازه‌ساخته‌شده به‌ازای هر rule توسط `snakemake --use-conda`، و زمان محاسباتی واقعی (ساعت‌ها، نه دقیقه‌ها، به‌خصوص برای مراحل nested CV و یادگیری عمیق). برای نحوهٔ دقیق اجرای آن‌ها به بخش ۱۱ مراجعه کنید.

---

## ۲. متادیتای موردنیاز برای تنظیمات فعلی

پایپلاین به ستون‌های زیر در `metadata/sample_metadata.tsv` نیاز دارد:

- `SampleID`، `Study`، `Group` — شناسه‌های اصلی مورد استفاده در کل پایپلاین.
- `Age`، `Sex` — مورد استفاده در `machine_learning.metadata_columns`.
- `Batch` — مورد استفاده در `confounding.batch` (اعتبارسنجی مستقل در preflight) و به‌عنوان ستون batch مستقل برای تشخیص‌ها.
- `Center` — مورد استفاده در تشخیص‌های `variance_partition`/`confounding` (اختیاری؛ در صورت نبود، اسکریپت‌ها آن را نادیده می‌گیرند).

`BMI` و `Smoking` در تنظیمات فعلی **الزامی نیستند**.

### برچسب‌های کلاس فعلی

```yaml
meta_analysis:
  reference_group: Control
  case_group: Disease
```

اگر گروه‌های زیستی شما نام‌های متفاوتی دارند، پیش از اجرا مقادیر مربوطه در config را به‌طور یکسان به‌روزرسانی کنید (`differential_abundance`، `meta_analysis`، `beta`، `permdisp`، `lefse`، `alpha_statistics`، `selbal`).

---

## ۳. فایل‌های ورودی موردنیاز

```text
metadata/sample_metadata.tsv
metadata/accessions.tsv
database/silva-138-99-classifier.qza
```

پایپلاین دادهٔ توالی‌یابی **paired-end** را انتظار دارد.

نکتهٔ مهم: این فایل‌ها باید **TSV خالص** باشند، نه یک فایل اکسل که با پسوند `.tsv` ذخیره شده باشد. برای بررسی: `file metadata/*.tsv` باید خروجی `ASCII text` بدهد، نه `Microsoft Excel` یا `Zip archive` (این دقیقاً مشکلی بود که در این مخزن پیدا و رفع شد).

---

## ۴. طبقه‌بند SILVA

```text
database/silva-138-99-classifier.qza
```

Preflight بررسی می‌کند که فایل وجود دارد، خالی نیست، یک آرشیو ZIP معتبر QZA است و ساختار داخلی مورد انتظار QIIME 2 را دارد.

---

## ۵. پلتفرم پیشنهادی

لینوکس توصیه می‌شود. در ویندوز از **WSL2** استفاده کنید.

---

## ۶. نصب ابزارها

### Snakemake

```bash
conda create -n microbiome-runner -c conda-forge -c bioconda python=3.11 snakemake
conda activate microbiome-runner
```

محیط‌های تحلیلی هر rule در `rules/envs/*.yaml` تعریف شده‌اند و هنگام استفاده از `--use-conda` به‌طور خودکار توسط Snakemake ساخته می‌شوند.

### QIIME 2

```bash
mamba create -p ./qiime2_env -c https://packages.qiime2.org/qiime2/2026.7/qiime2/released -c conda-forge -c bioconda qiime2=2026.7.0 q2cli=2026.7.0
```

> **اگر یک محیط conda از‌قبل‌ساخته‌شدهٔ QIIME 2 را به مسیر جدیدی منتقل/کپی می‌کنید** (همان اتفاقی که در این مخزن افتاده بود): تمام اسکریپت‌های زیر `bin/` (و برخی باینری‌های زیر `lib/`، به‌ویژه `Rscript`) مسیر قدیمی را به‌صورت هاردکد دارند و با خطای `cannot execute: required file not found` یا `No such file or directory` مواجه می‌شوند. برای رفع:
> - برای فایل‌های **متنی** (اسکریپت با خط `#!`): جایگزینی سادهٔ متن کافی و بی‌خطر است.
> - برای **باینری‌های کامپایل‌شده** (فایل‌های ELF که مسیر به‌صورت رشتهٔ با طول ثابت در آن‌ها جاسازی شده، مثل `Rscript`): رشتهٔ جایگزین باید با بایت‌های `NUL` در انتها پد شود تا طول دقیق بایت اصلی حفظ شود، وگرنه باینری خراب می‌شود. از ویرایشگر متنی ساده یا `sed` مستقیم روی این فایل‌ها استفاده نکنید.

---

## ۷. اعتبارسنجی پیش از اجرا

```bash
snakemake --use-conda --conda-frontend mamba --cores 1 -n
```

باید **۳۴۷ job** گزارش شود و با کد خروجی ۰ و بدون خطا تمام شود.

---

## ۸. اجرای کامل

```bash
cd MicrobiomePipeline
bash run_pipeline.sh 16        # یا تعداد هستهٔ CPU خودتان؛ پیش‌فرض ۸
```

`run_pipeline.sh` سه مرحله را خودکار اجرا می‌کند: (۱) اعتبارسنجی preflight، (۲) اجرای آزمایشی DAG، (۳) اجرای کامل پایپلاین. برای ازسرگیری یک اجرای نیمه‌تمام، همان دستور را دوباره اجرا کنید؛ اگر قفل باقی‌مانده باشد: `snakemake --unlock`.

---

## ۹. تنظیمات مهم DADA2

پارامترهای سراسری در `config/config.yaml` تعریف شده‌اند و باید پیش از اجرای واقعی بر اساس کیفیت و طول ریدهای هر مطالعه بررسی شوند. اگر کیفیت بین مطالعات متفاوت است، به‌جای تغییر مقادیر سراسری، از override اختصاصی هر batch استفاده کنید:

```yaml
dada2:
  batch_overrides:
    PRJEB39064:
      trunc_len_f: 230
      trunc_len_r: 190
```

هر پارامتری که برای یک batch مشخص نشود، از مقدار سراسری استفاده می‌کند.

---

## ۱۰. اجزای اصلی پایپلاین

دانلود SRA ← اعتبارسنجی SRA/FASTQ ← فشرده‌سازی ← Import در QIIME 2 ← DADA2 به‌ازای هر batch ← آمار denoising ← taxonomy ← فیلوژنی ← تنوع core/آلفا/بتا ← PERMANOVA/PERMDISP (مطالعه‌آگاه) ← Export جدول ویژگی/taxonomy ← فیلترینگ ← جایگزینی صفر ← نرمال‌سازی CLR ← تصحیح اثر Batch (MMUPHin) + تشخیص‌های قبل/بعد ← بررسی مخدوش‌کننده‌ها ← تفکیک واریانس ← **ANCOM-BC2** (روش اصلی) ← **ALDEx2** + **MaAsLin2** (مکمل) ← مقایسهٔ استحکام بین‌روشی ← LEfSe (تجمیعی + هر‌مطالعه + اجماع) ← Selbal (LOSO) ← اندازهٔ اثر هر مطالعه ← متاآنالیز اثرات تصادفی `metafor` ← نمودارهای forest/funnel/heatmap ← یادگیری ماشین کلاسیک (انتخاب ویژگی Boruta/ElasticNet/RF ← اجماع ← nested CV ← Optuna ← ارزیابی نهایی) ← یادگیری عمیق (nested CV ← ارزیابی نهایی ← تجسم ← تبیین‌پذیری) ← تحلیل حساسیت ML/DL روی دادهٔ تصحیح‌شده ← مقایسهٔ خام در برابر تصحیح‌شده ← **بستهٔ مقاله** ← **گزارش تکرارپذیری**.

---

## ۱۱. چه چیزی برای رسیدن به نتایج زیستی واقعی باقی مانده؟

این بازبینی همهٔ باگ‌های ساختاری/اتصالی پیداشده را رفع کرد و DAG و preflight را روی دادهٔ واقعی تأیید کرد، اما تحلیل کامل ۴۵ نمونه اجرا **نشد** (چون به ساعت‌ها زمان محاسباتی نیاز دارد و برای rule های مبتنی بر R، ساخت محیط‌های conda به‌خاطر بی‌ثباتی شبکه در این نشست کاملاً تکمیل نشد). برای رسیدن به نتایج واقعی:

۱. `conda activate microbiome-runner`
۲. `snakemake --use-conda --cores <N> -n` — تأیید کنید هنوز ۳۴۷ job و صفر خطا گزارش می‌شود.
۳. `bash run_pipeline.sh <N>` — بگذارید Snakemake محیط conda هر rule را در اولین استفاده بسازد (محیط‌های R/Bioconductor — ANCOM-BC2، ALDEx2، MaAsLin2، DESeq2، sva/MMUPHin — کندترین‌ها برای حل‌شدن هستند) و سپس کل DAG را اجرا کند.
۴. در پایان، `results/qc/preflight/preflight_checks.tsv`، `results/publication/manifest.tsv` و `results/reproducibility/reproducibility_summary.json` را بررسی کنید.

اگر هنگام ساخت یک محیط با خطای `SSL_read` یا "could not connect to server" مواجه شدید، این یک مشکل شبکه/mirror است نه باگ پایپلاین — دوباره تلاش کنید یا از mirror/شبکهٔ پایدارتری استفاده کنید.

---

## ۱۲. پوشه‌های خروجی اصلی

```text
results/qc/preflight/   results/qiime2/           results/export/
results/ancombc2/       results/aldex2/           results/maaslin2/
results/lefse/          results/selbal/           results/meta_analysis/
results/batch_effect/   results/machine_learning/ results/deep_learning/
results/publication/    results/reproducibility/
```

لاگ‌های اجرا: `logs/`. بنچمارک‌ها: `benchmark/`.

---

## ۱۳. چک‌لیست پیش از اجرا

- [ ] `metadata/sample_metadata.tsv` و `metadata/accessions.tsv` موجودند و **TSV خالص** هستند (نه فایل اکسل با پسوند `.tsv`).
- [ ] طبقه‌بند SILVA در `database/silva-138-99-classifier.qza` موجود است.
- [ ] SampleID ها و accession ها یکتا هستند؛ هر SampleID در متادیتا یک accession متناظر دارد و برعکس.
- [ ] `Study`، `Group`، `Age`، `Sex`، `Batch` پر شده‌اند؛ مقادیر `Group` دقیقاً با `reference_group`/`case_group` در config مطابقت دارند.
- [ ] همهٔ نمونه‌ها یک ناحیهٔ آمپلیکون/پرایمر مشترک دارند.
- [ ] داده‌های FASTQ به‌صورت paired-end هستند.
- [ ] تنظیمات trim/trunc در DADA2 با پروفایل کیفیت مطابقت دارند (در صورت تفاوت بین مطالعات، از `dada2.batch_overrides` استفاده کنید).
- [ ] `diversity.sampling_depth` پس از بررسی خروجی DADA2 منطقی است.
- [ ] حداقل ۳ مطالعهٔ واجد شرایط، ترجیحاً حداقل ۵ نمونهٔ Control و ۵ نمونهٔ Disease در هر مطالعه.
- [ ] `snakemake --use-conda --cores 1 -n` بدون خطا موفق می‌شود.
- [ ] Preflight با موفقیت رد می‌شود: `results/qc/preflight/preflight_validation.json` ← `"status": "PASS"`.
