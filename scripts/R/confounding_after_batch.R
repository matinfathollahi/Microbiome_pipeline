library(ggplot2)


args <- commandArgs(trailingOnly = TRUE)

metadata_file <- args[1]
batch <- args[2]
variables <- trimws(strsplit(args[3], ",")[[1]])
output_dir <- args[4]

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

############################################################
## Read metadata
############################################################

metadata <- read.delim(
    metadata_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

if (!(batch %in% colnames(metadata))) {
    stop("Batch column not found.")
}

metadata[[batch]] <- factor(metadata[[batch]])

############################################################

results_list <- list()
k <- 1

############################################################

for (v in variables) {

    if (!(v %in% colnames(metadata)))
        next

    tmp <- metadata[
        complete.cases(metadata[, c(batch, v)]),
    ]

    if (nrow(tmp) < 3)
        next

    if (length(unique(tmp[[batch]])) < 2)
        next

############################################################
## Categorical variables
############################################################

    if (!is.numeric(tmp[[v]])) {

        tab <- table(tmp[[batch]], tmp[[v]])

        if (nrow(tab) < 2 || ncol(tab) < 2)
            next

        if (any(tab < 5)) {

            test <- tryCatch(
                fisher.test(tab, simulate.p.value = TRUE),
                error = function(e) NULL
            )

            if (is.null(test))
                next

            statistic <- NA
            pvalue <- test$p.value
            test_name <- "Fisher"

        } else {

            test <- suppressWarnings(chisq.test(tab))

            statistic <- unname(test$statistic)
            pvalue <- test$p.value
            test_name <- "Chi-square"
        }



############################################################
## Numeric variables
############################################################

    } else {

        formula <- reformulate(batch, response = v)

        fit <- aov(
            formula,
            data = tmp
        )

        ## Check assumptions

        residuals_fit <- residuals(fit)

        normal_ok <- TRUE
        variance_ok <- TRUE


        ## Normality

        if (length(residuals_fit) >= 3 &&
            length(residuals_fit) <= 5000) {

            sh <- tryCatch(
                shapiro.test(residuals_fit),
                error=function(e) NULL
            )

            if (!is.null(sh)) {
                normal_ok <- sh$p.value > 0.05
            }
        }


        ## Homogeneity of variance

        lev <- tryCatch(
            car::leveneTest(
                formula,
                data = tmp
            ),
            error=function(e) NULL
        )


        if (!is.null(lev)) {

            variance_ok <- lev[["Pr(>F)"]][1] > 0.05

        }


        ################################################
        ## Choose test
        ################################################

        if (normal_ok && variance_ok) {


            anova_tab <- summary(fit)[[1]]

            statistic <- anova_tab[["F value"]][1]

            pvalue <- anova_tab[["Pr(>F)"]][1]

            test_name <- "ANOVA"


        } else {


            welch <- oneway.test(
                formula,
                data = tmp,
                var.equal = FALSE
            )


            statistic <- NA

            pvalue <- welch$p.value

            test_name <- "Welch ANOVA"

        }

    }

############################################################

    results_list[[k]] <- data.frame(
        Variable = v,
        Test = test_name,
        Statistic = statistic,
        Pvalue = pvalue,
        stringsAsFactors = FALSE
    )

    k <- k + 1
}

############################################################

if (length(results_list) == 0) {
    stop("No valid variables were available for testing.")
}

results <- do.call(rbind, results_list)

############################################################

results$FDR <- NA

idx <- !is.na(results$Pvalue)

results$FDR[idx] <- p.adjust(
    results$Pvalue[idx],
    method = "BH"
)

results$Significant <- results$FDR < 0.05

results$FDR_plot <- NA

results$FDR_plot[idx] <- pmax(
    results$FDR[idx],
    1e-300
)

############################################################

write.table(
    results,
    file.path(output_dir, "confounding_after.tsv"),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

############################################################
## Plot
############################################################

plot_results <- results[!is.na(results$FDR), ]

if (nrow(plot_results) > 0) {

    p <- ggplot(
        plot_results,
        aes(
            reorder(Variable, FDR),
            -log10(FDR_plot),
            fill = Significant
        )
    ) +
        geom_col(width = 0.8) +
        coord_flip() +
        theme_classic(base_size = 14) +
        scale_fill_manual(
            values = c(
                "TRUE" = "#D55E00",
                "FALSE" = "grey70"
            )
        ) +
        ylab("-log10(FDR)") +
        xlab("") +
        labs(fill = "FDR < 0.05")


    ggsave(
        file.path(output_dir, "confounding_after.pdf"),
        p,
        width = 8,
        height = 5
    )

    ggsave(
        file.path(output_dir, "confounding_after.png"),
        p,
        width = 8,
        height = 5,
        dpi = 300
    )
}

