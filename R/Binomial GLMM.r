# Load required libraries
library(dplyr)
library(lme4)
library(openxlsx)

# Prompt to select your dataset
file_path <- file.choose()

# Load the data
data <- read.csv(file_path, stringsAsFactors = TRUE)

# Check if the dataset has the required columns
required_columns <- c("Animal", "Condition", "Cups", "Total", "layer")
if (!all(required_columns %in% colnames(data))) {
  stop("The dataset must contain the following columns: Animal, Condition, Cups, Total, layer")
}

# Initialize a data frame to store results
results <- data.frame()

# Loop through unique layers
for (layer in unique(data$layer)) {
  # Filter data for the current layer
  layer_data <- filter(data, layer == !!layer)

  # Convert Animal and Condition to factors
  layer_data$Animal <- as.factor(layer_data$Animal)
  layer_data$Condition <- as.factor(layer_data$Condition)

  # Fit the GLMM using cbind to specify success and failure
  glmm_model <- glmer(cbind(Cups, Total - Cups) ~ Condition + (1 | Animal), 
                      family = binomial, data = layer_data)

  # Extract fixed effects summary
  fixed_effects <- summary(glmm_model)$coefficients

  # Convert fixed effects to a data frame for easier manipulation
  fixed_effects_df <- as.data.frame(fixed_effects)
  fixed_effects_df$Effect <- rownames(fixed_effects_df)
  
  # Append results for the layer (only interested in Condition effects)
  condition_effects <- fixed_effects_df[grepl("Condition", fixed_effects_df$Effect), ]
  condition_effects$Layer <- layer
  results <- rbind(results, condition_effects)
}

# Adjust p-values using Holm method
results$Adjusted_P_Sidak <- 1- (1 - results$`Pr(>|z|)`) ^ (length(results$`Pr(>|z|)`-1))


# Create the results folder if it doesn't exist
if (!dir.exists("results")) {
  dir.create("results")
}

# Save the results to a single sheet in an Excel file in the results folder
output_file <- file.path("results", paste0(tools::file_path_sans_ext(basename(file_path)), "_glmm.xlsx"))
write.xlsx(results, output_file, sheetName = "Fixed Effects Summary", rowNames = FALSE)

# Message to indicate where the file is saved
cat("Fixed effects summary saved to:", output_file, "\n")
