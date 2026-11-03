variable "name" {
  description = "Name of the budget."
  type        = string
}

variable "monthly_limit_usd" {
  description = "Monthly cost limit in US dollars."
  type        = number

  validation {
    condition     = var.monthly_limit_usd > 0
    error_message = "monthly_limit_usd must be greater than 0."
  }
}

variable "alert_emails" {
  description = "Email addresses that receive budget alerts."
  type        = list(string)

  validation {
    condition     = length(var.alert_emails) > 0
    error_message = "Provide at least one alert email."
  }
}

variable "actual_thresholds" {
  description = "Percentages of the limit at which an alert fires on actual spend."
  type        = list(number)
  default     = [50, 80, 100]
}

variable "forecast_threshold" {
  description = "Percentage of the limit at which an alert fires on forecasted spend."
  type        = number
  default     = 100
}
