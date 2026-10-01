---
name: azure-devops-cicd
description: Apply Azure DevOps CI/CD pipeline best practices — YAML pipeline structure, templates, environments and approvals, service connections, branch policies, and secret handling. Use when writing or reviewing Azure Pipelines YAML, designing release gates, or setting up build/release CI/CD.
---

# Azure DevOps CI/CD Best Practices

> **Provenance:** written from general knowledge, not sourced from Microsoft's
> official docs and not vendor-verified. No official Microsoft skill covering
> Azure DevOps CI/CD pipelines specifically was found — Microsoft's official
> Azure Skills Plugin covers Azure resource deployment/cost/diagnostics, not
> Azure DevOps pipelines. Cross-check against current Microsoft Learn docs
> before treating this as authoritative, and defer to a specific repo's own
> conventions where they differ.

Reference checklist for Azure Pipelines work. General guidance — an existing
org's actual pipeline conventions (naming, required checks, approval structure)
take precedence if they differ from this.

## YAML pipelines over Classic

- Use YAML pipelines (version-controlled alongside the code) rather than
  Classic (UI-configured, not in source control) for anything new.
- Structure as stages → jobs → steps; keep each stage's purpose clear (e.g.
  Build, Validate, Deploy-Dev, Deploy-Prod) rather than one flat job doing
  everything.

## Templates for reuse

- Extract shared logic (a standard build step, a standard Terraform
  validate/plan job) into templates (`extends`/`template` references) used
  across multiple repos' pipelines, instead of copy-pasting YAML per repo.
- Parameterize templates explicitly (typed parameters with defaults) rather
  than relying on implicit variable names being set correctly by the caller.

## Environments and approvals

- Define Azure DevOps Environments for each deployment target (dev/stage/prod)
  and attach approval checks to the ones that need a human gate — production
  should almost always require an approval, dev usually shouldn't.
- Use branch control and business hours checks on an environment where they
  matter, not just a manual approver.

## Service connections

- Scope each service connection to the minimum it needs (one Azure
  subscription/resource group, not a broad org-wide connection reused
  everywhere).
- Prefer workload identity federation (no stored secret) over a service
  principal with a stored client secret, where the target platform supports it.
- Restrict which pipelines/branches can use a production-scoped service
  connection (via its own approval/check settings).

## Secrets

- Variable groups linked to Azure Key Vault for secrets — never hardcoded in
  YAML or set as a plain (non-secret) pipeline variable.
- Mark pipeline variables that do hold sensitive values as secret explicitly,
  so they're masked in logs.

## Branch policies

- Require a PR (no direct pushes) into protected branches (main, release
  branches).
- Require at least one build validation check tied to the PR before merge.
- Require a minimum number of reviewers, and consider requiring a linked work
  item for traceability.
- Use path filters on triggers/validation checks so unrelated changes (e.g. a
  docs-only PR) don't force an unnecessary infra pipeline run.

## Artifacts and versioning

- Publish build artifacts with a clear, traceable version (build ID, semantic
  version, or commit SHA) — don't overwrite a mutable "latest" artifact for
  anything that gets deployed to production.

## Pipeline security

- Restrict who can approve production deployments and who can edit pipeline
  YAML for protected branches — a pipeline that deploys to production is
  effectively a production credential holder.
