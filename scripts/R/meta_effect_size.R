library(readr)
library(dplyr)

############################################################
## Command-line arguments
############################################################

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  stop("Usage: Rscript script.R input.tsv output.tsv")
}

input_file <- args[1]
output_file <- args[2]

############################################################
## Read input
############################################################

meta <- read.delim(
  input_file,
  check.names = FALSE,
  stringsAsFactors = FALSE
)

############################################################
## Convert numeric columns
############################################################

meta$EffectSize <- as.numeric(meta$EffectSize)
meta$StandardError <- as.numeric(meta$StandardError)

############################################################
## Basic QC
############################################################

meta <- meta %>%
  filter(
    !is.na(EffectSize),
    !is.na(StandardError),
    StandardError > 0
  )

############################################################
## Variance
############################################################

meta$Variance <- meta$StandardError^2

############################################################
## Weight
############################################################

meta$Weight <- 1 / meta$Variance

############################################################
## Z-score
############################################################

meta$Zscore <- meta$EffectSize / meta$StandardError

############################################################
## 95% Confidence Interval
############################################################

meta$Lower95 <- meta$EffectSize - 1.96 * meta$StandardError
meta$Upper95 <- meta$EffectSize + 1.96 * meta$StandardError

############################################################
## Write output
############################################################

write.table(
  meta,
  file = output_file,
  sep = "\t",
  quote = FALSE,
  row.names = FALSE,
  col.names = TRUE
)