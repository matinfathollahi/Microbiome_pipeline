library(ggplot2)
library(dplyr)

## -------------------------------
## Read arguments
## -------------------------------

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
    stop("Usage: Rscript lefse_plot.R <lefse_dir> <output_dir>")
}

lefse_dir  <- args[1]
output_dir <- args[2]

dir.create(output_dir,
           recursive = TRUE,
           showWarnings = FALSE)

## -------------------------------
## Read LEfSe results
## -------------------------------

input_file <- file.path(lefse_dir, "significant_taxa.tsv")

if (!file.exists(input_file)) {
    stop("Cannot find file:\n", input_file)
}

lefse <- read.delim(
    input_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

## -------------------------------
## Check columns
## -------------------------------

required_cols <- c("Taxon", "LDA", "Group")

missing_cols <- setdiff(required_cols, names(lefse))

if (length(missing_cols) > 0) {
    stop(
        "Missing columns: ",
        paste(missing_cols, collapse = ", ")
    )
}


## -------------------------------
## Handle no significant taxa
## -------------------------------

if (nrow(lefse) == 0) {

    placeholder_files <- c(
        "LDA_Barplot.pdf",
        "Dotplot.pdf",
        "Lollipop.pdf",
        "Effect_Size.pdf"
    )

    for (filename in placeholder_files) {

        pdf(
            file.path(
                output_dir,
                filename
            ),
            width = 8,
            height = 6
        )

        plot.new()

        text(
            0.5,
            0.58,
            "LEfSe Analysis",
            cex = 1.6,
            font = 2
        )

        text(
            0.5,
            0.48,
            "No significant taxa were detected.",
            cex = 1.2
        )

        text(
            0.5,
            0.40,
            "Analysis completed successfully.",
            cex = 1
        )

        dev.off()
    }

    writeLines(
        c(
            "LEfSe analysis completed successfully.",
            "No significant taxa were detected.",
            "No LDA effect-size plots were required."
        ),
        file.path(
            output_dir,
            "NO_SIGNIFICANT_TAXA.txt"
        )
    )

    message(
        "No significant taxa detected. ",
        "Placeholder plots were created."
    )

    quit(
        save = "no",
        status = 0
    )
}

## -------------------------------
## Order taxa
## -------------------------------

lefse <- lefse %>%
    arrange(desc(LDA))

lefse$Taxon <- factor(
    lefse$Taxon,
    levels = lefse$Taxon
)

## -------------------------------
## Common theme
## -------------------------------

plot_theme <-
    theme_bw(base_size = 12) +
    theme(
        legend.position = "right",
        panel.grid = element_blank()
    )

## -------------------------------
## 1. LDA Barplot
## -------------------------------

p1 <-
    ggplot(
        lefse,
        aes(
            Taxon,
            LDA,
            fill = Group
        )
    ) +
    geom_col(width = 0.75) +
    coord_flip() +
    labs(
        x = "",
        y = "LDA Score"
    ) +
    plot_theme

ggsave(
    file.path(output_dir, "LDA_Barplot.pdf"),
    p1,
    width = 8,
    height = 6
)

## -------------------------------
## 2. Dotplot
## -------------------------------

p2 <-
    ggplot(
        lefse,
        aes(
            LDA,
            Taxon,
            color = Group
        )
    ) +
    geom_point(size = 3) +
    labs(
        x = "LDA Score",
        y = ""
    ) +
    plot_theme

ggsave(
    file.path(output_dir, "Dotplot.pdf"),
    p2,
    width = 8,
    height = 6
)

## -------------------------------
## 3. Lollipop plot
## -------------------------------

p3 <-
    ggplot(
        lefse,
        aes(
            Taxon,
            LDA,
            color = Group
        )
    ) +
    geom_segment(
        aes(
            xend = Taxon,
            y = 0,
            yend = LDA
        ),
        linewidth = 0.8
    ) +
    geom_point(size = 3) +
    coord_flip() +
    labs(
        x = "",
        y = "LDA Score"
    ) +
    plot_theme

ggsave(
    file.path(output_dir, "Lollipop.pdf"),
    p3,
    width = 8,
    height = 6
)

## -------------------------------
## 4. Effect Size plot
## -------------------------------

p4 <-
    ggplot(
        lefse,
        aes(
            Taxon,
            abs(LDA),
            fill = Group
        )
    ) +
    geom_col(width = 0.7) +
    coord_flip() +
    labs(
        x = "",
        y = "Absolute LDA Score"
    ) +
    plot_theme

ggsave(
    file.path(output_dir, "Effect_Size.pdf"),
    p4,
    width = 8,
    height = 6
)

message("Plots saved to:")
message(output_dir)