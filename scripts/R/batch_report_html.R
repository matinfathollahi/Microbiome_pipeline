library(rmarkdown)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 8) {
  stop("Expected exactly 8 command-line arguments.")
}

summary_file     <- args[1]
pca_before       <- args[2]
pca_after        <- args[3]
pcoa_before      <- args[4]
pcoa_after       <- args[5]
variance_plot    <- args[6]
confounding_plot <- args[7]
output_html      <- args[8]

files <- c(
  summary_file,
  pca_before,
  pca_after,
  pcoa_before,
  pcoa_after,
  variance_plot,
  confounding_plot
)

missing_files <- files[!file.exists(files)]

if (length(missing_files) > 0) {
  stop(
    "Missing input files:\n",
    paste(missing_files, collapse = "\n")
  )
}

params <- list(
  summary_file     = normalizePath(summary_file),
  pca_before       = normalizePath(pca_before),
  pca_after        = normalizePath(pca_after),
  pcoa_before      = normalizePath(pcoa_before),
  pcoa_after       = normalizePath(pcoa_after),
  variance_plot    = normalizePath(variance_plot),
  confounding_plot = normalizePath(confounding_plot)
)

render(
  input = normalizePath("scripts/R/batch_report.Rmd"),
  output_file = basename(output_html),
  output_dir = dirname(output_html),
  params = params,
  envir = new.env(parent = globalenv())
)