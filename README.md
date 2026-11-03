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
- [x] M3 Scheduled GitHub Actions run that fails when something is found
- [x] M4 Tests (moto) and CI

## Scheduled scan (M3)

`.github/workflows/scan.yml` runs `scan.py --all-regions` every day and on demand. It assumes a read-only AWS role through GitHub OIDC, so no AWS keys are stored in GitHub. The job fails (and GitHub emails the owner) if anything billable is found.

The role can only list and describe EC2, load balancers, RDS and EKS. Its trust policy allows only this repository's `main` branch.

### Gotcha: immutable OIDC subject claims

Repositories created recently send a `sub` claim that includes numeric IDs, not the plain `repo:owner/name` form. A trust policy written with the plain form fails with "Not authorized to perform sts:AssumeRoleWithWebIdentity". Find your repo's real prefix with:

    gh api repos/OWNER/REPO/actions/oidc/customization/sub

and use `sub_claim_prefix` plus `:ref:refs/heads/main` in the role's trust policy.

## Status

![ci](https://github.com/fiehna-hue/aws-cost-guardrails/actions/workflows/ci.yml/badge.svg)
![scan](https://github.com/fiehna-hue/aws-cost-guardrails/actions/workflows/scan.yml/badge.svg)

## What I learned building this

- A scanner must say what it could not check. My first run reported "nothing found" while silently unable to list EKS clusters (the most expensive resource), so it now prints every skipped check.
- Tests that fake AWS (moto) let CI prove the scanner catches an unattached volume and a loose Elastic IP, without touching a real account.
- The Terraform budget module is validated and format-checked in CI but not applied by CI, because creating budgets needs permissions I deliberately do not give the pipeline.
- GitHub OIDC for newer repositories uses immutable subject claims; the trust policy must use the repo's `sub_claim_prefix`. Debugging that is documented above.
