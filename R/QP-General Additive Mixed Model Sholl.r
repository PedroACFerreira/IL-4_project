# Install and load necessary libraries
if (!requireNamespace("dplyr", quietly = TRUE)) install.packages("dplyr")
if (!requireNamespace("openxlsx", quietly = TRUE)) install.packages("openxlsx")
if (!requireNamespace("nlme", quietly = TRUE)) install.packages("nlme")

library(mgcv)
library(dplyr)
library(openxlsx)
library(nlme)

# Prompt user to select the dataset file
data_file_path <- file.choose()
cat("Selected dataset file:", data_file_path, "\n")

# Load and prepare the dataset
data <- read.csv(data_file_path)
cat("Data loaded successfully.\n")

data <- data %>%
  mutate(across(c(id, cell, cond, layer), as.factor),
         radius = as.numeric(radius),
         intersections = log(intersections + 1)) 

# Find the maximum radius value
max_radius <- max(data$radius, na.rm = TRUE)

# Define and ensure the Results directory exists
results_dir <- "Results"
if (!dir.exists(results_dir)) dir.create(results_dir)
cat("Results directory checked/created.\n")

# Define control parameters
control_params <- lmeControl(opt = "optim", msMaxIter = 500, msVerbose = FALSE)

# Parameters description
parameters_description <- data.frame(
  Parameter = c("Model Formula", "Random Effect Structure", "Correlation Structure", "Data", "Control Parameters"),
  Description = c(
    "intersections ~ cond * radius",
    "~ 1 | id/cell",
    "corAR1(form = ~ radius | id/cell)",
    paste("Data loaded from", basename(data_file_path)),
    "lmeControl(opt = 'optim', msMaxIter = 500, msVerbose = TRUE)"
  )
)

# Initialize lists to store results
results_by_radius <- list()
results_by_layer <- list()
original_model_summaries <- list()

# Fit the model by radius for the entire dataset
for (radius in 1:max_radius) {
  data_radius <- filter(data, radius == !!radius)
  
  fit_radius_model <- function() {
    tryCatch({
      lme(intersections ~ cond, 
          random = ~ 1 | id,
          data = data_radius,
          control = control_params)
    }, error = function(e) {
      NULL
    })
  }
  
  radius_model <- fit_radius_model()
  if (is.null(radius_model)) next
  
  radius_coefficients_df <- as.data.frame(summary(radius_model)$tTable)
  radius_coefficients_df$Term <- rownames(radius_coefficients_df)
  radius_coefficients_df$Radius <- radius
  radius_coefficients_df <- subset(radius_coefficients_df, grepl("condIL-4", Term))
  
  if (nrow(radius_coefficients_df) > 0) {
    results_by_radius[[as.character(radius)]] <- radius_coefficients_df
  }
}

# Combine all radius-specific results and apply multiple comparison corrections
combined_radius_results_df <- bind_rows(results_by_radius) %>%
  mutate(
    Adjusted_P_Holm = p.adjust(`p-value`, method = "holm"),
    Adjusted_P_Sidak = 1 - (1 - `p-value`) ^ length(`p-value`)
  )

cat("Fitting original model\n")
fit_original_model <- function() {
  tryCatch({
        gamm(intersections ~ cond + s(radius, by = cond, bs = "tp") ,  # Include spline for radius
                   random = list(cell = ~ 1 | id/cell),  # Random intercept for cell within id
                   correlation = corAR1(form = ~ radius | id/cell), # Autoregressive correlation
                   data = data,
                   family = quasipoisson(link = "identity"))
  }, error = function(e) {
    print(e)
  })
}

original_model <- fit_original_model()

if (!is.null(original_model)) {
  summary_table <- summary(original_model$gam)$p.table
  original_model_coefficients_df <- as.data.frame(summary_table)
  original_model_coefficients_df$Term <- rownames(original_model_coefficients_df)
  original_model_coefficients_df <- subset(original_model_coefficients_df, grepl("condIL-4", Term))
} else {
  original_model_coefficients_df <- data.frame()
}
print(original_model_coefficients_df)

# Separate data by layer and perform analysis
for (layer in unique(data$layer)) {
  data_layer <- filter(data, layer == !!layer)
  layer_radius_results <- list()
  
  for (radius in 1:max_radius) {
    data_radius <- filter(data_layer, radius == !!radius)
    
    fit_radius_model <- function() {
      tryCatch({
        lme(intersections ~ cond, 
            random = ~ 1 | id,
            data = data_radius,
            control = control_params)
      }, error = function(e) {
        NULL
      })
    }
    
    radius_model <- fit_radius_model()
    if (is.null(radius_model)) next
    
    radius_coefficients_df <- as.data.frame(summary(radius_model)$tTable)
    radius_coefficients_df$Term <- rownames(radius_coefficients_df)
    radius_coefficients_df$Radius <- radius
    radius_coefficients_df$Layer <- layer
    radius_coefficients_df <- subset(radius_coefficients_df, grepl("condIL-4", Term))
    
    if (nrow(radius_coefficients_df) > 0) {
      layer_radius_results[[as.character(radius)]] <- radius_coefficients_df
    }
  }
  
  if (length(layer_radius_results) > 0) {
    combined_layer_results_df <- bind_rows(layer_radius_results) %>%
      mutate(
        Adjusted_P_Holm = p.adjust(`p-value`, method = "holm"),
        Adjusted_P_Sidak = 1 - (1 - `p-value`) ^ length(`p-value`)
      )
    
    results_by_layer[[as.character(layer)]] <- combined_layer_results_df
    
    fit_layer_model <- function() {
      tryCatch({
        gamm(intersections ~ cond + s(radius, by = cond, bs = "tp") ,  # Include spline for radius
                   random = list(cell = ~ 1 | id/cell),  # Random intercept for cell within id
                   correlation = corAR1(form = ~ radius | id/cell), # Gaussian correlation
                   data = data_layer,
                   family = quasipoisson(link = "identity"))
      }, error = function(e) {
        print(e)
      })
    }
    
    layer_model <- fit_layer_model()
    if (!is.null(layer_model)) {
      summary_table <- summary(layer_model$gam)$p.table
      layer_model_coefficients_df <- as.data.frame(summary_table)
      layer_model_coefficients_df$Term <- rownames(layer_model_coefficients_df)
      layer_model_coefficients_df$Layer <- layer
      layer_model_coefficients_df <- subset(layer_model_coefficients_df, grepl("condIL-4", Term))
      
      if (nrow(layer_model_coefficients_df) > 0) {
        original_model_summaries[[as.character(layer)]] <- layer_model_coefficients_df
      }
    }
  }
}

# Create a workbook to save results
wb <- createWorkbook()

# Add sheets to the workbook
addWorksheet(wb, "Mixed_Model")
writeDataTable(wb, "Mixed_Model", original_model_coefficients_df)

addWorksheet(wb, "Radius_Specific_Summary")
writeDataTable(wb, "Radius_Specific_Summary", combined_radius_results_df)

for (layer in unique(data$layer)) {
  addWorksheet(wb, paste0("Layer_", layer, "_Summary"))
  writeDataTable(wb, paste0("Layer_", layer, "_Summary"), results_by_layer[[as.character(layer)]])
  
  addWorksheet(wb, paste0("Mixed_Model_Layer_", layer))
  writeDataTable(wb, paste0("Mixed_Model_Layer_", layer), original_model_summaries[[as.character(layer)]])
}

addWorksheet(wb, "Parameters_Description")
writeData(wb, "Parameters_Description", parameters_description, headerStyle = createStyle(textDecoration = "bold"))

# Save the workbook
combined_summary_file_name <- paste0("Mixed_Model_", gsub(".csv", "", basename(data_file_path)), ".xlsx")
saveWorkbook(wb, file = file.path(results_dir, combined_summary_file_name), overwrite = TRUE)
cat("Combined summary coefficients, original model results, and parameters saved to", combined_summary_file_name, "\n")

