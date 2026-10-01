# CLAUDE.md

This file is the router for Terraform/AWS IaC and Azure DevOps pipeline work.
It doesn't hold code — it points at real repos on this machine and tracks what's
actually been decided about them, so a new session doesn't start from zero.

## Vault Structure

See `setup.md` for the full folder layout and the naming convention to use when
creating anything new (a project folder, a knowledge note, an ADR). In short:

- `00-System/` — `Current-Focus.md` (tiny, overwritten snapshot) and
  `Retrieval-Questions.md` (what this vault actually needs to answer).
- `01-Projects/<name>/` — one per real project, created on demand, never
  pre-created speculatively. Holds repo overview notes, `decisions/` (ADRs),
  `troubleshooting/`.
- `02-Knowledge/<topic>/` — created only once a topic is genuinely studied from
  real work, not pre-filled.
- `06-Templates/` — canonical templates for repo overviews, ADRs, troubleshooting.
- `.claude/skills/` — `terraform-style-guide` (HashiCorp's official Terraform
  skill) and `aws-iam` (AWS's official IAM skill) are vendored from their
  official vendor repos, unmodified — see `THIRD_PARTY_SKILLS.md` for source
  and license. `azure-devops-cicd` is community-sourced, not vendor-official —
  see its own header. These load automatically when relevant, but they're
  general guidance, not a substitute for a specific repo's own conventions.

## Note Format

Notes follow Obsidian conventions, but they are plain Markdown — no Obsidian install
is needed. Every note has YAML frontmatter, and related notes are linked with
`[[wikilinks]]` using the vault-relative path (`[[01-Projects/<project>/decisions/ADR-001-title|ADR-001]]`).
Only link to notes that exist. `setup.md` has the full rules.

## Core Principle

> If it didn't actually happen, don't document it as if it did.

Never fabricate a decision, a result, a root cause, or claim a pipeline/module
"works" unless it was actually confirmed. Say plainly when something is a plan,
a recommendation, or untested — don't write it as if it already happened.

## Known Repos

Tracked in `config.yaml` (this vault's own folder), not inline here — keeps real
repo paths out of this file, and out of git if this vault's repo is public.

- `config.example.yaml` — committed, placeholders only. This is what a public repo holds.
- `config.yaml` — gitignored, the real list. Copy the example to this filename and
  fill in real values the first time this vault is set up on a machine.

If `config.yaml` doesn't exist yet, that means this vault hasn't been set up on this
machine yet — copy `config.example.yaml` to `config.yaml` before doing anything else.

## Decisions Log

<!-- Append short entries here when a real Terraform/pipeline decision gets made.
     Don't backfill decisions that weren't actually made yet. -->

### YYYY-MM-DD — `<repo-name>`: <short decision title>

**Context:** <what problem this addressed>
**Decision:** <what was actually decided>
**Why:** <the real reason — not a guess>

## Session Behavior

- At the start of a session, read this file, `config.yaml` (if it exists) and
  `00-System/Current-Focus.md` — that's enough context. Don't go re-reading every
  repo unless the task actually names one.
- Before ending a session that made real progress, **overwrite** (don't append to)
  `00-System/Current-Focus.md`: what's active, what changed, what's next. Keep it
  short. A session that only answered questions and changed no files doesn't update it.
- When a new repo shows up to work on, follow `setup.md`: add an entry to
  `config.yaml`, create its overview note under `01-Projects/`, then work at its
  real path — before doing anything else in it.
- When a non-trivial Terraform/pipeline decision gets made, append an entry to
  **Decisions Log** — only after it's actually decided, not while still weighing options.
- Each individual repo may have its own `CLAUDE.md` with its own conventions —
  this file governs routing and decision tracking; a repo's own file governs how
  to work in that repo's code.

## Security & Data Handling

<!-- Confirm with your organization's policy before relying on this daily. Do not commit this
     file with the placeholders below filled in with real values to a PUBLIC repo. -->

- Claude surface in use: `<TBD — Team/Enterprise / Claude Code+org key / Bedrock / Azure>`
- Never write AWS access keys, secret keys, Azure DevOps PATs, connection strings, or
  any credential into this file or `config.yaml`. Use placeholders: `<ACCOUNT_ID>`,
  `<SUBSCRIPTION_ID>`, `<PAT>`, `<ORG_NAME>`, `<REPO_URL>`.
- Record decisions and patterns, not pasted proprietary specifics — no internal system
  names, customer data, or unreleased business details beyond what's already fine to
  write down under your organization's policy.
- This file's template (with placeholder rows/entries, no real values) is fine in a
  public repo. The moment real repo paths, decisions, or org-specific detail get filled
  in, that copy belongs somewhere private that matches your organization's policy — not committed
  back to the public template repo.

## Writing Style

Technical, concise, honest, written by whoever did the work. No corporate buzzwords or marketing language.
