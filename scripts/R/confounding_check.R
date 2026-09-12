library(ggplot2)

args <- commandArgs(trailingOnly = TRUE)

if(length(args) < 4){
    stop(
        paste(
            "Missing arguments.\n",
            "Usage: Rscript script.R <metadata_file> <batch> <variables> <output_dir>"
        )
    )
}

metadata_file <- args[1]
batch <- args[2]
variables <- strsplit(args[3], ",")[[1]]
output_dir <- args[4]

metadata <- read.delim(
    metadata_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

metadata[[batch]] <- as.factor(metadata[[batch]])

results <- data.frame()

for(v in variables){

    if(!(v %in% colnames(metadata))){
        warning(paste(v, "not found in metadata"))
        next
    }

    tmp <- metadata[
        complete.cases(metadata[, c(batch, v)]),
    ]

    if(nrow(tmp) == 0){
        next
    }

    ############################################
    ## Categorical variable
    ############################################

    if(
        is.character(tmp[[v]]) ||
        is.factor(tmp[[v]]) ||
        length(unique(tmp[[v]])) <= 5
    ){

        tab <- table(
            tmp[[batch]],
            tmp[[v]]
        )

        expected <- suppressWarnings(
            chisq.test(tab)$expected
        )

        if(any(expected < 5)){

            test <- fisher.test(tab, simulate.p.value = TRUE, B = 10000)

            test_name <- "Fisher"

            statistic <- NA

        }else{

            test <- chisq.test(tab)

            test_name <- "Chi-square"

            statistic <- unname(test$statistic)

        }

        results <- rbind(
            results,
            data.frame(
                Variable = v,
                Test = test_name,
                Statistic = statistic,
                Pvalue = test$p.value
            )
        )

    }else{


############################################
## Numeric variable
############################################

        # Check number of batch groups
        if(length(unique(tmp[[batch]])) < 2){
            next
        }

        # Check sample size per batch
        group_sizes <- table(tmp[[batch]])

        if(any(group_sizes < 3)){
            warning(
                paste(
                    "Skipping", v,
                    "- some batch groups have <3 samples"
                )
            )
            next
        }


        formula <- as.formula(
            paste(v, "~", batch)
        )


        # Fit ANOVA
        fit <- aov(
            formula,
            data = tmp
        )

        # Check variance homogeneity
        group_var <- tapply(
            tmp[[v]],
            tmp[[batch]],
            var
        )

        if(
            any(is.na(group_var)) ||
            any(group_var == 0)
        ){
            variance_ok <- FALSE
        }else{
            variance_ok <- max(group_var) /
                           min(group_var) < 4
        }



        # Check residual normality
        shapiro_p <- tryCatch(
            shapiro.test(residuals(fit))$p.value,
            error = function(e) NA
        )


        # If assumptions fail use Kruskal-Wallis
        if(
            (!is.na(shapiro_p) && shapiro_p < 0.05) ||
            !variance_ok
        ){

            kw <- kruskal.test(
                formula,
                data = tmp
            )

            results <- rbind(
                results,
                data.frame(
                    Variable = v,
                    Test = "Kruskal-Wallis",
                    Statistic = unname(kw$statistic),
                    Pvalue = kw$p.value
                )
            )

            next
        }


        sm <- summary(fit)[[1]]

        results <- rbind(
            results,
            data.frame(
                Variable = v,
                Test = "ANOVA",
                Statistic = sm[["F value"]][1],
                Pvalue = sm[["Pr(>F)"]][1]
            )
        )


    } 

} 


#################################################
## FDR correction
#################################################

if(nrow(results) == 0){
    stop("No valid variables tested")
}

results$FDR <- p.adjust(
    results$Pvalue,
    method = "BH"
)

results$FDR[
    results$FDR < 1e-300
] <- 1e-300

#################################################
## Save table
#################################################

write.table(
    results,
    file.path(
        output_dir,
        "confounding_results.tsv"
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

#################################################
## Plot
#################################################

results$Significant <- results$FDR < 0.05

p <- ggplot(
    results,
    aes(
        reorder(
            Variable,
            FDR
        ),
        -log10(FDR),
        fill = Significant
    )
) +
    geom_col(width = 0.8) +
    coord_flip() +
    theme_classic(base_size = 14) +
    xlab("") +
    ylab("-log10(FDR)") +
    theme(
        legend.position = "right"
    )

ggsave(
    file.path(
        output_dir,
        "confounding.pdf"
    ),
    p,
    width = 8,
    height = 5
)