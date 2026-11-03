provider "aws" {
  region = "us-east-1"
}

module "budget" {
  source = "../../modules/budget"

  name              = "monthly-guardrail"
  monthly_limit_usd = 20
  alert_emails      = ["you@example.com"]
}

output "budget_name" {
  value = module.budget.budget_name
}
