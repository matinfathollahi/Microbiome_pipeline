library(ggplot2)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
    stop(
        "Usage: Rscript alpha_plots.R <alpha_dir> <metadata_file> <output_dir>"
    )
}

alpha_dir <- args[1]
metadata_file <- args[2]
output_dir <- args[3]

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

if (!file.exists(metadata_file)) {
    stop("Metadata file not found: ", metadata_file)
}

metadata <- read.delim(
    metadata_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

required_metadata <- c(
    "SampleID",
    "Group"
)

missing_metadata <- setdiff(
    required_metadata,
    colnames(metadata)
)

if (length(missing_metadata) > 0) {
    stop(
        "Missing metadata columns: ",
        paste(missing_metadata, collapse = ", ")
    )
}


metrics <- list(

    faith_pd = list(
        label = "Faith's PD",
        filename = "Faith_PD_Boxplot.pdf"
    ),

    shannon = list(
        label = "Shannon diversity",
        filename = "Shannon_Boxplot.pdf"
    ),

    evenness = list(
        label = "Pielou's evenness",
        filename = "Evenness_Boxplot.pdf"
    ),

    observed_features = list(
        label = "Observed features",
        filename = "Observed_Features_Boxplot.pdf"
    )
)


for (metric in names(metrics)) {

    metric_file <- file.path(
        alpha_dir,
        metric,
        "alpha-diversity.tsv"
    )

    if (!file.exists(metric_file)) {
        stop(
            "Alpha diversity file not found: ",
            metric_file
        )
    }

    alpha <- read.delim(
        metric_file,
        check.names = FALSE,
        stringsAsFactors = FALSE
    )

    if (ncol(alpha) < 2) {
        stop(
            "Invalid alpha diversity file: ",
            metric_file
        )
    }

    colnames(alpha)[1:2] <- c(
        "SampleID",
        "Value"
    )

    alpha$SampleID <- as.character(
        alpha$SampleID
    )

    metadata$SampleID <- as.character(
        metadata$SampleID
    )

    plot_data <- merge(
        alpha[, c("SampleID", "Value")],
        metadata,
        by = "SampleID"
    )

    plot_data <- plot_data[
        !is.na(plot_data$Value) &
        !is.na(plot_data$Group),
    ]

    if (nrow(plot_data) == 0) {
        stop(
            "No valid samples available for metric: ",
            metric
        )
    }

    plot_data$Group <- factor(
        plot_data$Group
    )

    p <- ggplot(
        plot_data,
        aes(
            x = Group,
            y = Value,
            fill = Group
        )
    ) +
        geom_boxplot(
            outlier.shape = NA
        ) +
        geom_jitter(
            width = 0.15,
            alpha = 0.7,
            size = 2
        ) +
        theme_classic() +
        theme(
            legend.position = "none"
        ) +
        labs(
            title = metrics[[metric]]$label,
            x = "Group",
            y = metrics[[metric]]$label
        )

    ggsave(
        filename = file.path(
            output_dir,
            metrics[[metric]]$filename
        ),
        plot = p,
        width = 7,
        height = 5
    )

    message(
        "Created plot for: ",
        metric
    )
}

message(
    "All alpha-diversity plots completed."
)