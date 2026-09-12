library(ggplot2)
library(dplyr)

#-----------------------------
# Read command-line arguments
#-----------------------------
args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 3) {
  stop("Usage: Rscript pca.R counts.tsv metadata.tsv output_dir")
}

table_file <- args[1]
metadata_file <- args[2]
output_dir <- args[3]

#-----------------------------
# Check input files
#-----------------------------
if (!file.exists(table_file))
  stop("Count table not found.")

if (!file.exists(metadata_file))
  stop("Metadata file not found.")

dir.create(output_dir,
           recursive = TRUE,
           showWarnings = FALSE)

#-----------------------------
# Read data
#-----------------------------
counts <- read.delim(
  table_file,
  row.names = 1,
  check.names = FALSE
)

metadata <- read.delim(
  metadata_file,
  check.names = FALSE
)

#-----------------------------
# Check metadata columns
#-----------------------------
if (!"SampleID" %in% colnames(metadata))
  stop("Metadata must contain a 'SampleID' column.")

if (!"Group" %in% colnames(metadata))
  stop("Metadata must contain a 'Group' column.")

#-----------------------------
# Transpose count table
# Samples × Features
#-----------------------------
counts <- t(counts)

counts <- as.data.frame(counts)

#-----------------------------
# Remove missing values
#-----------------------------
counts[is.na(counts)] <- 0

# Ensure numeric values
counts[] <- lapply(counts, as.numeric)

# Remove zero-variance features
counts <- counts[, apply(counts, 2, var) > 0]

#-----------------------------
# Log transformation
# Recommended for count data
#-----------------------------
counts <- log1p(counts)

#-----------------------------
# PCA
#-----------------------------
pca <- prcomp(
  counts,
  center = TRUE,
  scale. = TRUE
)

#-----------------------------
# PCA scores
#-----------------------------
scores <- as.data.frame(pca$x)

scores$SampleID <- rownames(scores)

scores <- left_join(
  scores,
  metadata,
  by = "SampleID"
)

#-----------------------------
# Save scores
#-----------------------------
write.table(
  scores,
  file.path(output_dir, "pca_scores.tsv"),
  sep = "\t",
  quote = FALSE,
  row.names = FALSE
)

#-----------------------------
# PCA loadings
#-----------------------------
loadings <- as.data.frame(pca$rotation)

loadings$ASV <- rownames(loadings)

write.table(
  loadings,
  file.path(output_dir, "pca_loadings.tsv"),
  sep = "\t",
  quote = FALSE,
  row.names = FALSE
)

#-----------------------------
# Explained variance
#-----------------------------
variance <- data.frame(
  PC = paste0("PC", seq_along(pca$sdev)),
  Variance = (pca$sdev^2 / sum(pca$sdev^2)) * 100
)

write.table(
  variance,
  file.path(output_dir, "pca_variance.tsv"),
  sep = "\t",
  quote = FALSE,
  row.names = FALSE
)

#-----------------------------
# PCA Plot
#-----------------------------
xlabel <- sprintf(
  "PC1 (%.2f%%)",
  variance$Variance[1]
)

ylabel <- sprintf(
  "PC2 (%.2f%%)",
  variance$Variance[2]
)

p <- ggplot(
  scores,
  aes(
    x = PC1,
    y = PC2,
    color = Group
  )
) +
  geom_point(size = 3) +
  labs(
    x = xlabel,
    y = ylabel,
    title = "Principal Component Analysis"
  ) +
  theme_bw(base_size = 14) +
  theme(
    legend.title = element_blank(),
    plot.title = element_text(hjust = 0.5)
  )

ggsave(
  filename = file.path(output_dir, "pca.pdf"),
  plot = p,
  width = 7,
  height = 6,
  dpi = 300
)