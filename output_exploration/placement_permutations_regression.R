args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
script_dir <- if (length(file_arg) > 0) {
  dirname(normalizePath(sub("^--file=", "", file_arg[[1]])))
} else {
  getwd()
}

candidate_data_paths <- c(
  file.path(script_dir, "placement_permutations_area_diagnostics.csv"),
  file.path(getwd(), "placement_permutations_area_diagnostics.csv"),
  file.path(getwd(), "output_exploration", "placement_permutations_area_diagnostics.csv")
)
data_path <- candidate_data_paths[file.exists(candidate_data_paths)][1]
if (is.na(data_path)) {
  stop(
    "Missing placement_permutations_area_diagnostics.csv. ",
    ". Run the notebook through the CSV export cell first.",
    call. = FALSE
  )
}
script_dir <- dirname(normalizePath(data_path))

install.packages("pacman", repos = "https://cloud.r-project.org")
pacman::p_load(
  dplyr,
  ggplot2,
  sandwich,
  tidyverse
)

df <- read_csv(data_path, stringsAsFactors = FALSE)
df$log_total_nodes <- log1p(df$total_nodes)
df$log_total_population <- log1p(df$total_population)
df$log_within_xx <- log1p(df$within_xx)
df$log_within_xy <- log1p(df$within_xy)
df$log_within_yy <- log1p(df$within_yy)

standardize_predictors <- function(model_df, predictors) {
  for (predictor in predictors) {
    predictor_mean <- mean(model_df[[predictor]], na.rm = TRUE)
    predictor_sd <- sd(model_df[[predictor]], na.rm = TRUE)
    if (!is.finite(predictor_sd) || predictor_sd == 0) {
      model_df[[predictor]] <- 0
    } else {
      model_df[[predictor]] <- (model_df[[predictor]] - predictor_mean) / predictor_sd
    }
  }
  model_df
}

hc3_coefficients <- function(fit, model_name) {
  estimates <- coef(fit)
  keep <- !is.na(estimates)
  estimates <- estimates[keep]
  design <- model.matrix(fit)[, keep, drop = FALSE]
  residuals <- residuals(fit)
  leverage <- hatvalues(fit)
  omega <- residuals^2 / (1 - leverage)^2
  bread <- tryCatch(
    solve(crossprod(design)),
    error = function(error) qr.solve(crossprod(design))
  )
  vcov_hc3 <- bread %*% crossprod(design, design * omega) %*% bread
  robust_se <- sqrt(diag(vcov_hc3))
  t_value <- estimates / robust_se
  degrees_freedom <- df.residual(fit)
  critical_value <- qt(0.975, df = degrees_freedom)

  data.frame(
    model = model_name,
    term = names(estimates),
    standardized_coef = unname(estimates),
    robust_se = unname(robust_se),
    t_value = unname(t_value),
    p_value = unname(2 * pt(abs(t_value), df = degrees_freedom, lower.tail = FALSE)),
    conf_low = unname(estimates - critical_value * robust_se),
    conf_high = unname(estimates + critical_value * robust_se),
    row.names = NULL
  )
}

fit_standardized_lm <- function(data, response, predictors, model_name) {
  model_df <- data[, c(response, predictors), drop = FALSE]
  model_df <- model_df[complete.cases(model_df), , drop = FALSE]
  model_df <- standardize_predictors(model_df, predictors)
  fit <- lm(reformulate(predictors, response = response), data = model_df)

  list(
    name = model_name,
    fit = fit,
    predictors = predictors,
    model_df = model_df,
    coefficients = hc3_coefficients(fit, model_name),
    comparison = data.frame(
      model = model_name,
      n = nobs(fit),
      r_squared = summary(fit)$r.squared,
      adj_r_squared = summary(fit)$adj.r.squared,
      aic = AIC(fit),
      bic = BIC(fit),
      row.names = NULL
    )
  )
}

response <- "spread_similarity"
predictor_sets <- list(
  controls = c("total_x", "edge_density", "log_total_nodes"),
  controls_black_count_cv = c("total_x", "edge_density", "log_total_nodes", "black_count_cv"),
  controls_black_share_cv = c("total_x", "edge_density", "log_total_nodes", "black_share_cv"),
  controls_total_pop_cv = c("total_x", "edge_density", "log_total_nodes", "total_pop_cv"),
  combined_simple = c(
    # "total_x",
    "edge_density",
    "log_total_nodes",
    "black_count_cv",
    # "black_share_cv",
    "total_pop_cv"
  ),
  controls_within_raw_products = c(
    # "total_x",
    "edge_density",
    "log_total_nodes",
    "within_xx",
    "within_xy",
    "within_yy"
  ),
  combined_within_log_products = c(
    # "total_x",
    "edge_density",
    "log_total_nodes",
    "black_count_cv",
    # "black_share_cv",
    "total_pop_cv",
    "log_within_xx",
    "log_within_xy",
    "log_within_yy"
  ),
  combined_within_shares = c(
    # "total_x",
    "edge_density",
    "log_total_nodes",
    "black_count_cv",
    # "black_share_cv",
    "total_pop_cv",
    "within_xx_share_perm_mean",
    "within_xy_share_perm_mean",
    "within_yy_share_perm_mean"
  )
)

models <- lapply(
  names(predictor_sets),
  function(model_name) {
    fit_standardized_lm(df, response, predictor_sets[[model_name]], model_name)
  }
)
names(models) <- names(predictor_sets)

model_comparison <- do.call(rbind, lapply(models, function(model) model$comparison))
model_comparison <- model_comparison[order(-model_comparison$adj_r_squared), ]

coefficient_table <- do.call(rbind, lapply(models, function(model) model$coefficients))

comparison_path <- file.path(script_dir, "placement_permutations_regression_model_comparison.csv")
coefficient_path <- file.path(script_dir, "placement_permutations_regression_coefficients.csv")
plot_path <- file.path(script_dir, "placement_permutations_regression_plots.pdf")

write.csv(model_comparison, comparison_path, row.names = FALSE)
write.csv(coefficient_table, coefficient_path, row.names = FALSE)

cat("\nModel comparison:\n")
print(model_comparison, row.names = FALSE)
cat("\nWrote:\n")
cat(" - ", comparison_path, "\n", sep = "")
cat(" - ", coefficient_path, "\n", sep = "")

pdf(plot_path, width = 11, height = 8.5)
par(mfrow = c(2, 2), mar = c(4.2, 4.2, 3.2, 1.2))

barplot(
  setNames(model_comparison$adj_r_squared, model_comparison$model),
  las = 2,
  ylab = "Adjusted R-squared",
  main = "Model comparison"
)

combined <- models[["combined_simple"]]
combined_df <- combined$model_df
combined_df$predicted <- predict(combined$fit)
plot(
  combined_df$predicted,
  combined_df[[response]],
  xlab = "Predicted spread_similarity",
  ylab = "Observed spread_similarity",
  main = "Combined simple model",
  pch = 19,
  col = "gray35"
)
abline(0, 1, lty = 2, col = "gray45")

plot(
  df$black_count_cv,
  df$spread_similarity,
  xlab = "Black count CV",
  ylab = "spread_similarity",
  main = "Direct count-variance check",
  pch = 19,
  col = "gray35"
)
lines(lowess(df$black_count_cv, df$spread_similarity), col = "#4C78A8", lwd = 2)

coef_plot <- subset(coefficient_table, model == "combined_simple" & term != "(Intercept)")
coef_plot <- coef_plot[order(coef_plot$standardized_coef), ]
y_pos <- seq_len(nrow(coef_plot))
plot(
  coef_plot$standardized_coef,
  y_pos,
  xlim = range(c(coef_plot$conf_low, coef_plot$conf_high), na.rm = TRUE),
  yaxt = "n",
  ylab = "",
  xlab = "Standardized coefficient",
  main = "Combined simple coefficients",
  pch = 19,
  col = "#4C78A8"
)
segments(coef_plot$conf_low, y_pos, coef_plot$conf_high, y_pos, col = "gray30", lwd = 1.5)
axis(2, at = y_pos, labels = coef_plot$term, las = 2)
abline(v = 0, lty = 2, col = "gray45")

dev.off()
cat(" - ", plot_path, "\n", sep = "")
