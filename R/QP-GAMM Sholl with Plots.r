# -------------------------------- HEADER SECTION ---------------------------------
# GAMM Model and Plotting Script
# This script loads a dataset, fits a GAMM model with splines for radius,
# and generates multiple diagnostic plots, including a QQ plot, 
# Residuals vs Fitted plot, and Fitted vs Observed plot.
# The combined plots will be saved in a single image, and the Fitted vs Observed
# plot will also be saved separately.

# -------------------------------- LIBRARY SETUP ---------------------------------
# Install and load necessary libraries
if (!requireNamespace("mgcv", quietly = TRUE)) install.packages("mgcv")
if (!requireNamespace("dplyr", quietly = TRUE)) install.packages("dplyr")
if (!requireNamespace("ggplot2", quietly = TRUE)) install.packages("ggplot2")
if (!requireNamespace("openxlsx", quietly = TRUE)) install.packages("openxlsx")
if (!requireNamespace("cowplot", quietly = TRUE)) install.packages("cowplot")
if (!requireNamespace("splines2", quietly = TRUE)) install.packages("splines2")

library(mgcv)
library(dplyr)
library(ggplot2)
library(openxlsx)
library(splines)
library(cowplot)



# -------------------------------- DATA PREPARATION ---------------------------------
# Prompt user to select the dataset file
data_file_path <- file.choose()
csv_filename <- tools::file_path_sans_ext(basename(data_file_path))  # Extract the base filename
cat("Selected dataset file:", csv_filename, "\n")

# Load and prepare the dataset
data <- read.csv(data_file_path)
cat("Data loaded successfully.\n")

data <- data %>%
  mutate(across(c(id, cell, cond, layer), as.factor),
         radius = as.numeric(radius),
         intersections = log(intersections+1))

# Optional filtering step, comment out if not needed
#data <- filter(data, layer == !!"PCL")

# -------------------------------- PLOT AVERAGES ---------------------------------
# Calculate averages for plotting
averages <- aggregate(intersections ~ radius + cond, data = data, FUN = mean)

# Create the average plot for each condition
average_plot <- ggplot(averages, aes(x = radius, y = intersections, color = cond)) +
  geom_line(linewidth = 1) + 
  geom_point(size = 3) +
  labs(title = "Average Intersections at Each Radius for Ctrl vs IL-4",
       x = "Radius", y = "Average Intersections", color = "Condition") +
  theme_minimal() +
  theme(legend.position = "top") +
  scale_color_manual(values = c("Ctrl" = "#edbfd9", "IL-4" = "#afdab3")) +
  theme(plot.title = element_text(hjust = 0.5),
        panel.background = element_rect(fill = "white"))



# -------------------------------- FIT GAMM MODEL ---------------------------------
# Fit the GAMM model
gamm_model <- gamm(intersections ~ cond + s(radius, by = cond, bs = "tp"),  
                   correlation = corAR1(form = ~ radius | id/cell),  
                   data = data,
                   family = quasipoisson(link = "identity")
                   )

# Extract fixed effects coefficients
fixed_effects <- summary(gamm_model$gam)
print(fixed_effects)

# Calculate AIC and BIC
aic_value <- AIC(gamm_model$lme)  # AIC from the mixed model
bic_value <- BIC(gamm_model$lme)  # BIC from the mixed model

# Print AIC and BIC values
cat("AIC:", aic_value, "\n")
cat("BIC:", bic_value, "\n")

# -------------------------------- FITTED VS OBSERVED PLOT ---------------------------------
# Create new data for predictions
radius_seq <- seq(min(data$radius), max(data$radius), length.out = 100)
new_data <- expand.grid(radius = radius_seq, cond = unique(data$cond))

# Make predictions based on the GAMM model
new_data$fitted_log <- predict(gamm_model$gam, newdata = new_data, type = "link")
new_data$fitted <- exp(new_data$fitted_log) - 1  # Transform back to original scale

# Create the Fitted vs Observed plot
fitted_vs_observed_plot <- ggplot(data, aes(x = radius, y = exp(intersections), color = cond)) +
  geom_point(alpha = 0.5, size = 2) +
  geom_line(data = new_data, aes(y = fitted, linetype = cond), linewidth = 1) +
  theme_minimal(base_size = 15) +
  labs(title = "Fitted GAMM vs Observed Data (Original Scale)",
       x = "Radius", y = "Intersections (Adjusted +1)") +
  scale_color_manual(values = c("Ctrl" = "#edbfd9", "IL-4" = "#afdab3")) +
  theme(panel.background = element_rect(fill = "white"),
        plot.title = element_text(hjust = 0.5))

# -------------------------------- RESIDUALS VS FITTED PLOT ---------------------------------
# Extract fitted values and residuals
fitted_values <- fitted(gamm_model$lme)
residuals <- residuals(gamm_model$lme)

# Create the Residuals vs Fitted plot
residuals_vs_fitted_plot <- ggplot(data.frame(fitted = fitted_values, residuals = residuals), 
                                   aes(x = fitted, y = residuals)) +
  geom_point(size = 2) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "red") +
  labs(title = "Residuals vs Fitted", x = "Fitted Values", y = "Residuals") +
  theme_minimal(base_size = 15) +
  theme(panel.background = element_rect(fill = "white"),
        plot.title = element_text(hjust = 0.5))

# -------------------------------- DIAGNOSTICS: QQ PLOT (Mimicking Base R) ---------------------------------
qq_plot <- ggplot(data = data.frame(sample_quantiles = residuals), aes(sample = sample_quantiles)) +
  stat_qq(size = 1.5) +
  stat_qq_line(color = "red", linewidth = 1) +
  labs(title = "QQ Plot of Residuals") +
  theme_minimal(base_size = 15) +
  theme(panel.background = element_rect(fill = "white"),
        plot.title = element_text(hjust = 0.5))

# -------------------------------- COMBINE PLOTS WITH COWPLOT ---------------------------------
# Combine all diagnostic plots into one
combined_plot <- plot_grid(average_plot, fitted_vs_observed_plot, residuals_vs_fitted_plot, qq_plot, 
                           labels = c("A", "B", "C", "D"), ncol = 2, align = 'v') +
  theme(plot.background = element_rect(fill = "grey92", colour = NA))

# Save the combined plot
combined_plot_file <- paste0("Results/Plots/", csv_filename, "_combined_plots.png")
ggsave(combined_plot_file, plot = combined_plot, width = 16, height = 12, dpi = 300)
cat("Combined plot saved as", combined_plot_file, "\n")

# Save Fitted vs Observed plot separately
fitted_vs_observed_file <- paste0("Results/Plots/", csv_filename, "_fitted_vs_observed.png")
ggsave(fitted_vs_observed_file, plot = fitted_vs_observed_plot, width = 8, height = 6, dpi = 300)
cat("Fitted vs Observed plot saved as", fitted_vs_observed_file, "\n")

# Plot QQ Plot
qqnorm(residuals(gamm_model$gam, type = "pearson"))
qqline(residuals(gamm_model$gam, type = "pearson"))

# Plot Histogram of Residuals
hist(residuals(gamm_model$gam, type = "pearson"), breaks = 20, main = "Histogram of Pearson Residuals", xlab = "Pearson Residuals")


