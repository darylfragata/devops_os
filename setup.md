# Setup & Naming Conventions

This file is for Claude Code (or any AI tool reading `CLAUDE.md`) — it's the
reference for what already exists after a plain `git clone`, and what naming
convention to follow when creating anything new later. A human setting this up
only needs the three steps in `README.md`; this file is the detail behind them.

## What already exists after cloning

No AI session is needed to get the base structure — it's committed as-is:

```
devops_os/
├── CLAUDE.md
├── README.md
├── setup.md
├── config.example.yaml       # copy to config.yaml, fill in real repo paths
├── .gitignore
├── 00-System/
│   ├── Current-Focus.md      # tiny, overwritten snapshot
│   └── Retrieval-Questions.md
├── 01-Projects/               # empty — one subfolder per real project, created on demand
├── 02-Knowledge/              # empty — one subfolder per topic, created only once genuinely studied
├── 06-Templates/
│   ├── repo-overview-template.md
│   ├── adr-template.md
│   └── troubleshooting-template.md
└── .claude/
    └── skills/
        ├── terraform-style-guide/   # vendored from hashicorp/agent-skills — see THIRD_PARTY_SKILLS.md
        ├── aws-iam/                 # vendored from aws/agent-toolkit-for-aws — see THIRD_PARTY_SKILLS.md
        └── azure-devops-cicd/       # community-sourced, not vendor-official — see its SKILL.md header
```

## Naming convention for anything created later

**`01-Projects/<name>/`** — one folder per real project (a project can bundle
several repos). `<name>` is the project's actual name, kebab-case, matching how
it's referred to by your team — not the AI's choice, ask if it's ambiguous. Inside:

- `README.md` — one per real on-disk repo the project bundles, from
  `06-Templates/repo-overview-template.md`. If the project is a single repo,
  one `README.md` is enough; if it bundles multiple repos, use
  `01-Projects/<name>/<repo-name>/README.md`, one subfolder per repo, named
  exactly after the real repo.
- `decisions/` — ADRs, from `06-Templates/adr-template.md`, named
  `ADR-NNN-short-kebab-title.md`, numbered sequentially, never renumbered even
  when superseded.
- `troubleshooting/` — from `06-Templates/troubleshooting-template.md`, short
  descriptive kebab-case filenames, created only when something real gets
  debugged, not speculatively.

**`02-Knowledge/<topic>/`** — created only once a topic is genuinely studied
independent of any one project (e.g. a Terraform pattern that came up in one
project but is generally true). `<topic>` is a plain, specific name (e.g.
`terraform-state-management`, not `terraform` — see `.claude/skills/` for the
broad reference material; this folder is for what was actually learned from
real work, not a restatement of the skills).

## Note format: Obsidian-style, no Obsidian needed

Notes are written the way Obsidian expects, but they are plain Markdown files, so
nothing needs to be installed. Opening the folder in Obsidian later just works.
When creating or editing any note under `00-System/`, `01-Projects/` or `02-Knowledge/`:

- **Frontmatter on every note** — a YAML block at the top with at least `title`,
  `type` (`index`, `adr`, `troubleshooting`, `knowledge`), `date` and `tags`. The
  templates in `06-Templates/` already have it; copy it, don't invent new fields.
- **Link related notes with `[[wikilinks]]`**, not Markdown links:
  - `[[01-Projects/<project>/decisions/ADR-001-short-title]]` — vault-relative
    path, no `.md`. Use the full path so it can't be ambiguous.
  - `[[path/to/note|short label]]` — a label for reading.
  - `[[path/to/note#Heading]]` — a link to one heading in that note.
- **Only link to a note that exists.** A link to a note that was never written is a
  claim that it was; if the note is still planned, say that in plain text instead.
- **Link where it helps a reader get to the next note**: a repo overview to its
  ADRs and troubleshooting notes, an ADR to the note it supersedes, a troubleshooting
  note to the ADR it led to. Don't add links just to have links.
- Each template ends with a `## Related` section for these links. Leave it out
  when there is nothing real to link, don't fill it with placeholders.
- Tags are lowercase, kebab-case, in the frontmatter `tags` list. Keep them few.

Use ordinary Markdown links only for external URLs and for files that are not
notes (for example `config.example.yaml`).

## Adding a new repo

Before doing any real work in a new repo, in order:

1. Add an entry to `config.yaml` (not `config.example.yaml`) with its real path.
2. Create its overview note at `01-Projects/<project>/README.md` (or
   `01-Projects/<project>/<repo-name>/README.md` if the project bundles more
   than one repo) from `06-Templates/repo-overview-template.md`.
3. Only then start the actual work, at the repo's real path — never inside
   this vault.
