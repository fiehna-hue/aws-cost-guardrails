# aws-cost-guardrails

Read-only tooling to catch the AWS resources that quietly keep billing you after a lab or project is "finished".

## scan.py

Checks one region (or all of them) for: running EC2 instances, unattached EBS volumes, unassociated Elastic IPs, NAT gateways, load balancers, RDS instances and EKS clusters. It never changes or deletes anything.

    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python3 scan.py                 # one region (default us-east-1)
    python3 scan.py --all-regions   # every enabled region

Exit code is 1 when something billable is found, 0 when clean, so it can run in CI.

If your credentials lack permission for a check, the scanner prints `skipped` instead of pretending the account is clean.

## Roadmap

- [x] M1 Scanner
- [x] M2 Terraform module: budget with email alerts at 50%, 80%, 100%
- [ ] M3 Scheduled GitHub Actions run that fails when something is found
- [ ] M4 Tests and demo write-up
