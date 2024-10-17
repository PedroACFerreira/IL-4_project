# ===================================================================
# Script Purpose: 
# This script analyzes a dataset containing measurements for various 
# parameters related to different conditions (Ctrl vs IL-4) across 
# multiple animals. It fits linear mixed models for each parameter 
# to assess the effect of the condition, outputs the results to an 
# Excel file, and generates QQ plots for model diagnostics.
# 
# Model Parameters:
# - Fixed effect: condition (with IL-4 as the reference level)
# - Random effect: animal (to account for different cells within the same animal)
# ===================================================================

# List of required packages
required_packages <- c("readr", "dplyr", "lmerTest", "broom.mixed", "multcomp", "openxlsx", "ggplot2", "cowplot", "pacman")

# Function to install packages if not already installed
install_if_missing <- function(package) {
  if (!require(package, character.only = TRUE)) {
    install.packages(package, dependencies = TRUE)
    library(package, character.only = TRUE)
    message(paste("Package", package, "installed and loaded."))
  }
}

# Install required packages
lapply(required_packages, install_if_missing)

# Load required packages
lapply(required_packages, require, character.only = TRUE)

# Set condition name for analysis; "condIL-4" is the reference level
cond_name <- "condIL-4"

# Prompt user to choose a CSV file for analysis
file_path <- file.choose()

# Extract dataset name from the file path
dataset_name <- tools::file_path_sans_ext(basename(file_path))

# Function to read the CSV file and preprocess the data
read_data <- function(file_path) {
  read_csv(file_path, show_col_types = FALSE) %>%
    mutate(across(c(animal, cell), as.factor),  # Convert animal and cell to factors
           # Apply log transformation to parameters using log1p (log(x + 1))
           across(c(ConvexHull, Solidity, IBA_1, Sphericity, Ramifications, MaxRadius), log1p))  
}

data <- read_data(file_path)

# List of parameters to analyze
parameters <- c("SA.V", "ConvexHull", "Solidity", "IBA_1", "Sphericity", "Ramifications", "MaxRadius")

# Function to fit mixed models and collect results
fit_model <- function(param, data) {
  # Set control parameters for optimization
  control_params <- lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 100000))
  
  # Fit the model and suppress the boundary singular fit message
  output <- capture.output({
    model <- lmer(as.formula(paste(param, "~ cond + (1 | animal)")), 
                  data = data, 
                  control = control_params)
  }, type = "message")
  
  # Check if the output contains the singular fit message
  if (isSingular(model)) {
    message(paste("Boundary singular fit for parameter:", param))
  }

  # Extract summary with p-values using lmerTest
  summary_model <- summary(model)

  # Convert fixed effects to a data frame
  fixed_effects <- as.data.frame(summary_model$coefficients)
  
  # Get results specifically for condIL-4
  if (cond_name %in% rownames(fixed_effects)) {
    cond_results <- fixed_effects[cond_name, ]
    
    # Store the results in a data frame
    list(
      results = data.frame(
        Parameter = param,
        Estimate = cond_results["Estimate"],
        Std.Error = cond_results["Std. Error"],
        dF = summary_model$coefficients[cond_name, "df"],
        Statistic = cond_results["t value"],
        P.Value = as.numeric(cond_results["Pr(>|t|)"])
      ),
      model = model
    )
  } else {
    warning(paste("No results found for", param))
    return(NA)
  }
}

# Apply the fit_model function to each parameter
fit_results <- lapply(parameters, fit_model, data = data)

# Extract models and results from the fit_results
models <- lapply(fit_results, function(res) res$model)
results <- do.call(rbind, lapply(fit_results, function(res) res$results))

# Multiple comparison correction using Sidak method
results$P.Corrected_Sidak <- ifelse(!is.na(results$P.Value), 1 - (1 - results$P.Value) ^ nrow(results), NA)

# Write results to a single Excel sheet with dataset name
write.xlsx(results, file = paste0("Results/", dataset_name, "_mixed_model.xlsx"), 
           sheetName = "Results", rowNames = FALSE)

# Function to create QQ plots for model diagnostics
create_qq_plot <- function(model, param) {
  
  # Create QQ plot
  ggplot(data = data.frame(residuals = resid(model)), aes(sample = residuals)) +
    geom_qq() +
    geom_qq_line() +
    labs(title = paste("QQ Plot for", param),
         x = "Theoretical Quantiles",
         y = "Sample Quantiles") +
    theme_minimal(base_size = 15) +
    theme(plot.background = element_rect(fill = "#eeeeee"))  # Light grey background
}

# Generate QQ plots for each parameter and model
qq_plots <- mapply(create_qq_plot, model = models, param = parameters, SIMPLIFY = FALSE)

# Combine all QQ plots into one
combined_qq_plot <- plot_grid(plotlist = qq_plots, ncol = 2)  # Adjust ncol as needed

# Save the combined QQ plot with dataset name
ggsave(paste0("Results/Plots/", dataset_name, "_QQ_plots.png"), 
       combined_qq_plot, width = 12, height = 8, dpi = 300)  # Larger image
