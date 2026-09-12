library(dplyr)
library(metafor)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 9) {
    stop(
        paste(
            "Usage: Rscript alpha_statistics.R",
            "<alpha_dir>",
            "<metadata_file>",
            "<output_dir>",
            "<study_column>",
            "<reference_group>",
            "<case_group>",
            "<min_samples_per_group>",
            "<min_studies>",
            "<meta_method>"
        )
    )
}

alpha_dir <- args[1]
metadata_file <- args[2]
output_dir <- args[3]

study_column <- args[4]
reference_group <- args[5]
case_group <- args[6]

min_samples_per_group <- as.integer(args[7])
min_studies <- as.integer(args[8])

meta_method <- args[9]

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

if (!file.exists(metadata_file)) {
    stop(
        "Metadata file not found: ",
        metadata_file
    )
}

metadata <- read.delim(
    metadata_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

required_metadata <- c(
    "SampleID",
    "Group",
    study_column
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

metadata$SampleID <- as.character(
    metadata$SampleID
)


metrics <- list(

    faith_pd = "Faith_PD",

    shannon = "Shannon",

    evenness = "Evenness",

    observed_features = "Observed_Features"

)


summary_results <- data.frame()
meta_summary_results <- data.frame()


for (metric in names(metrics)) {

    metric_name <- metrics[[metric]]

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

    alpha$Value <- as.numeric(
        alpha$Value
    )

    data <- left_join(
        alpha[, c("SampleID", "Value")],
        metadata,
        by = "SampleID"
    )

    data <- data %>%
        filter(
            !is.na(Value),
            !is.na(Group),
            !is.na(.data[[study_column]]),
            Group %in% c(reference_group, case_group)
        )

    data$Group <- factor(
        data$Group,
        levels = c(
            reference_group,
            case_group
        )
    )

    data$Study <- as.character(
        data[[study_column]]
    )

    eligible_studies <- data %>%
        group_by(Study) %>%
        summarise(
            N_Control = sum(Group == reference_group),
            N_Case = sum(Group == case_group),
            .groups = "drop"
        ) %>%
        filter(
            N_Control >= min_samples_per_group,
            N_Case >= min_samples_per_group
        )


    data_meta <- data %>%
        filter(
            Study %in% eligible_studies$Study
        )

    if (length(unique(as.character(data$Group))) < 2) {
        stop(
            "Both groups are required for metric: ",
            metric_name
        )
    }



    if (nrow(eligible_studies) < min_studies) {
        warning(
            "Metric ", metric_name,
            " has only ", nrow(eligible_studies),
            " eligible studies; minimum required = ",
            min_studies
        )
    }

    # -------------------------
    # Kruskal-Wallis
    # -------------------------

    kw <- kruskal.test(
        Value ~ Group,
        data = data
    )

    kw_result <- data.frame(
        Metric = metric_name,
        Statistic = unname(
            kw$statistic
        ),
        DF = unname(
            kw$parameter
        ),
        Pvalue = kw$p.value
    )

    write.table(
        kw_result,
        file = file.path(
            output_dir,
            paste0(
                metric_name,
                "_Kruskal.tsv"
            )
        ),
        sep = "\t",
        row.names = FALSE,
        quote = FALSE
    )


    # -------------------------
    # Pairwise Wilcoxon
    # -------------------------

    pairwise <- pairwise.wilcox.test(
        x = data$Value,
        g = data$Group,
        p.adjust.method = "BH",
        exact = FALSE
    )

    write.table(
        pairwise$p.value,
        file = file.path(
            output_dir,
            paste0(
                metric_name,
                "_Wilcoxon.tsv"
            )
        ),
        sep = "\t",
        quote = FALSE,
        col.names = NA
    )


    # -------------------------
    # Group descriptive stats
    # -------------------------

    descriptive <- data %>%
        group_by(Group) %>%
        summarise(
            N = n(),
            Mean = mean(
                Value,
                na.rm = TRUE
            ),
            SD = sd(
                Value,
                na.rm = TRUE
            ),
            Median = median(
                Value,
                na.rm = TRUE
            ),
            IQR = IQR(
                Value,
                na.rm = TRUE
            ),
            .groups = "drop"
        )

    descriptive$Metric <- metric_name

    descriptive <- descriptive[
        ,
        c(
            "Metric",
            "Group",
            "N",
            "Mean",
            "SD",
            "Median",
            "IQR"
        )
    ]

    write.table(
        descriptive,
        file = file.path(
            output_dir,
            paste0(
                metric_name,
                "_Descriptive.tsv"
            )
        ),
        sep = "\t",
        row.names = FALSE,
        quote = FALSE
    )






# -------------------------
# Study-aware meta-analysis
# -------------------------

eligible_file <- file.path(
    output_dir,
    paste0(
        metric_name,
        "_Eligible_Studies.tsv"
    )
)

write.table(
    eligible_studies,
    file = eligible_file,
    sep = "\t",
    row.names = FALSE,
    quote = FALSE
)


if (nrow(eligible_studies) >= min_studies) {

    # -------------------------
    # Study-specific statistics
    # -------------------------

    study_stats <- data_meta %>%
        group_by(Study, Group) %>%
        summarise(
            N = sum(!is.na(Value)),
            Mean = mean(
                Value,
                na.rm = TRUE
            ),
            SD = sd(
                Value,
                na.rm = TRUE
            ),
            Median = median(
                Value,
                na.rm = TRUE
            ),
            IQR = IQR(
                Value,
                na.rm = TRUE
            ),
            .groups = "drop"
        )


    # -------------------------
    # Case statistics
    # -------------------------

    case_stats <- study_stats %>%
        filter(
            Group == case_group
        ) %>%
        transmute(
            Study,
            N_Case = N,
            Mean_Case = Mean,
            SD_Case = SD,
            Median_Case = Median,
            IQR_Case = IQR
        )


    # -------------------------
    # Reference statistics
    # -------------------------

    reference_stats <- study_stats %>%
        filter(
            Group == reference_group
        ) %>%
        transmute(
            Study,
            N_Reference = N,
            Mean_Reference = Mean,
            SD_Reference = SD,
            Median_Reference = Median,
            IQR_Reference = IQR
        )


    # -------------------------
    # Combine study statistics
    # -------------------------

    effects_input <- inner_join(
        case_stats,
        reference_stats,
        by = "Study"
    )


    # Remove studies where SMD cannot
    # be estimated reliably
    effects_input <- effects_input %>%
        filter(
            N_Case >= min_samples_per_group,
            N_Reference >= min_samples_per_group,
            is.finite(Mean_Case),
            is.finite(Mean_Reference),
            is.finite(SD_Case),
            is.finite(SD_Reference),
            !(SD_Case == 0 & SD_Reference == 0)
            
        )


    if (nrow(effects_input) >= min_studies) {

        # -------------------------
        # Hedges' g per study
        # -------------------------

        effects <- metafor::escalc(
            measure = "SMD",

            m1i = Mean_Case,
            sd1i = SD_Case,
            n1i = N_Case,

            m2i = Mean_Reference,
            sd2i = SD_Reference,
            n2i = N_Reference,

            data = effects_input
        )


        effects$Hedges_g <- effects$yi
        effects$Variance <- effects$vi
        effects$SE <- sqrt(
            effects$vi
        )

        effects$CI95_Low <-
            effects$yi -
            qnorm(0.975) *
            effects$SE

        effects$CI95_High <-
            effects$yi +
            qnorm(0.975) *
            effects$SE

        effects$Pvalue <-
            2 * pnorm(
                -abs(
                    effects$yi /
                    effects$SE
                )
            )

        effects$Metric <- metric_name

        effects$Comparison <- paste0(
            case_group,
            " vs ",
            reference_group
        )


        # -------------------------
        # Save study effects
        # -------------------------

        write.table(
            effects,
            file = file.path(
                output_dir,
                paste0(
                    metric_name,
                    "_Study_Effects.tsv"
                )
            ),
            sep = "\t",
            row.names = FALSE,
            quote = FALSE
        )


        # -------------------------
        # Random-effects model
        # -------------------------

        meta_fit <- metafor::rma(
            yi = yi,
            vi = vi,
            data = effects,
            method = meta_method
        )


        meta_result <- data.frame(

            Metric = metric_name,

            Comparison = paste0(
                case_group,
                " vs ",
                reference_group
            ),

            K = meta_fit$k,

            Hedges_g = as.numeric(
                coef(meta_fit)[1]
            ),

            SE = meta_fit$se,

            CI95_Low = meta_fit$ci.lb,

            CI95_High = meta_fit$ci.ub,

            Pvalue = meta_fit$pval,

            Tau2 = meta_fit$tau2,

            I2 = meta_fit$I2,

            Q = meta_fit$QE,

            Q_Pvalue = meta_fit$QEp,

            stringsAsFactors = FALSE
        )


        # -------------------------
        # Save meta result
        # -------------------------

        write.table(
            meta_result,
            file = file.path(
                output_dir,
                paste0(
                    metric_name,
                    "_Meta.tsv"
                )
            ),
            sep = "\t",
            row.names = FALSE,
            quote = FALSE
        )


        # -------------------------
        # Forest plot
        # -------------------------

        pdf(
            file.path(
                output_dir,
                paste0(
                    metric_name,
                    "_Forest.pdf"
                )
            ),
            width = 8,
            height = max(
                6,
                0.45 * nrow(effects) + 3
            )
        )

        metafor::forest(
            meta_fit,
            slab = effects$Study,
            xlab = paste0(
                "Hedges' g (",
                case_group,
                " - ",
                reference_group,
                ")"
            ),
            header = c(
                "Study",
                "Hedges' g [95% CI]"
            )
        )

        dev.off()


        # -------------------------
        # Add to combined meta summary
        # -------------------------

        meta_summary_results <- rbind(
            meta_summary_results,
            meta_result
        )

    } else {

        warning(
            "Not enough valid studies after SD/effect-size checks for metric: ",
            metric_name
        )
    }

} else {

    warning(
        "Not enough eligible studies for meta-analysis of metric: ",
        metric_name
    )
}














    summary_results <- rbind(
        summary_results,
        kw_result
    )

    message(
        "Statistics completed for: ",
        metric
    )
}



# -------------------------
# Combined meta-analysis summary
# -------------------------

if (nrow(meta_summary_results) > 0) {

    meta_summary_results$FDR <- p.adjust(
        meta_summary_results$Pvalue,
        method = "BH"
    )

    write.table(
        meta_summary_results,
        file = file.path(
            output_dir,
            "Alpha_Meta_Summary.tsv"
        ),
        sep = "\t",
        row.names = FALSE,
        quote = FALSE
    )
}

# -------------------------
# Combined summary
# -------------------------

summary_results$FDR <- p.adjust(
    summary_results$Pvalue,
    method = "BH"
)

write.table(
    summary_results,
    file = file.path(
        output_dir,
        "Alpha_Kruskal_Summary.tsv"
    ),
    sep = "\t",
    row.names = FALSE,
    quote = FALSE
)

message(
    "All alpha-diversity statistics completed."
)