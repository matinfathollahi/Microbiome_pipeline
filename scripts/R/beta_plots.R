library(ggplot2)
library(readr)
library(dplyr)

ordination <- read.delim(
  "results/export/pcoa/bray_curtis/ordination.txt",
  comment.char = "#"
)

metadata <- read.delim(
  "metadata/sample_metadata.tsv"
)

plot_data <- left_join(
  ordination,
  metadata,
  by = "SampleID"
)

dir.create(
  "results/figures/beta",
  recursive = TRUE,
  showWarnings = FALSE
)

p <- ggplot(
  plot_data,
  aes(
    x = PC1,
    y = PC2,
    color = Group
  )
) +
  geom_point(size = 3) +
  stat_ellipse(level = 0.95) +
  theme_classic() +
  theme(text = element_text(size = 14))

ggsave(
  filename = "results/figures/beta/bray_curtis_pcoa.pdf",
  plot = p,
  width = 8,
  height = 6
)