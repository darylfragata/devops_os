# Third-Party Skills

Skills vendored into `.claude/skills/` from official vendor repos, kept as-is
(unmodified) with their original license included in each folder.

| Skill | Source | Commit | License |
|---|---|---|---|
| `terraform-style-guide` | [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills), `plugins/terraform/skills/terraform-style-guide` | `c2d65df` | MPL-2.0 (see `terraform-style-guide/LICENSE`) |
| `aws-iam` | [aws/agent-toolkit-for-aws](https://github.com/aws/agent-toolkit-for-aws), `skills/core-skills/aws-iam` | `68d9e85` | Apache-2.0 (see `aws-iam/LICENSE`, `aws-iam/NOTICE`) |

`azure-devops-cicd` is not vendored from an official source — see its own
`SKILL.md` header for provenance.

## Why only these two AWS/Terraform skills

Both official repos are large collections of narrow, service-specific skills,
not one broad "best practices" skill. `terraform-style-guide` and `aws-iam`
were picked because they match this vault's actual use case (Terraform IaC on
AWS) most directly — `aws-iam` in particular includes IAM baseline-policy
generation from a Terraform plan JSON. Other skills in those repos
(`aws-security` = Security Hub/GuardDuty finding triage, `aws-networking` =
Route 53/CloudFront/Transit Gateway routing, `aws-deployment` = AWS
CodePipeline/CodeBuild — not applicable since this vault's CI/CD is Azure
DevOps) didn't match closely enough to justify pulling in. Add more from
either repo later if a real need shows up — don't pre-pull the rest
speculatively.

## Keeping these current

These are pinned to a commit, not auto-updating. Re-clone the source repo and
re-copy the skill folder (keeping `LICENSE`/`NOTICE`) periodically, or when a
real gap shows up — no automation for this yet.
