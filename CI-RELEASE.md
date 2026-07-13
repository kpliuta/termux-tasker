# CI & Release Process

This document describes the automated CI checks and release workflow for the
termux-tasker project.

---

## Overview

Every pull request targeting `main` is validated by CI checks. When a PR is
merged (squash merge), a release workflow automatically bumps the version,
updates the changelog, creates a git tag, and publishes a GitHub Release.

```
  PR opened/updated
        │
        ▼
  ┌─────────────┐
  │  CI checks  │  (tests, mypy, autoflake, changelog)
  └──────┬──────┘
         │ must pass
         ▼
  ┌─────────────┐
  │  PR title   │  (conventional commit format)
  │  validation │
  └──────┬──────┘
         │ must pass
         ▼
     PR merged
    (squash)
         │
         ▼
  ┌──────────────┐
  │   Release    │  (version bump, changelog, tag, GitHub Release)
  │   workflow   │
  └──────────────┘
```

---

## Repository Setup (Required)

Before the workflows can function, two repository settings must be configured.

### 1. Enable squash merge only

The release workflow depends on squash merge — the PR title becomes the single
commit message on `main`, which is parsed for the version bump type.

Go to **Settings → General → Pull Requests** and:

- [ ] **Allow squash merging** — checked
- [ ] **Allow merge commits** — unchecked
- [ ] **Allow rebase merging** — unchecked

Or via CLI:

```bash
gh api repos/{owner}/{repo} \
  --method PATCH \
  --field allow_merge_commit=false \
  --field allow_rebase_merge=false \
  --field allow_squash_merge=true
```

### 2. Enable read/write permissions for GITHUB_TOKEN

The release workflow needs to push commits, create tags, and create
GitHub Releases. The default `GITHUB_TOKEN` must have write access.

Go to **Settings → Actions → General → Workflow permissions** and:

- [ ] Select **Read and write permissions**
- [ ] Check **Allow GitHub Actions to create and approve pull requests**

Or via CLI:

```bash
gh api repos/{owner}/{repo}/actions/permissions/workflow \
  --method PUT \
  --field default_workflow_permissions=write \
  --field can_approve_pull_request_reviews=true
```

---

## Conventional Commits

All PR titles **must** follow the
[Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<optional scope>): <description>
```

### Types

| Type       | Version bump | Description                                   |
|------------|--------------|-----------------------------------------------|
| `feat`     | minor        | A new feature                                 |
| `fix`      | patch        | A bug fix                                     |
| `docs`     | patch        | Documentation only changes                    |
| `style`    | patch        | Formatting, missing semicolons, etc.          |
| `refactor` | patch        | Code change that fixes no bug/adds no feature |
| `perf`     | patch        | Performance improvement                       |
| `test`     | patch        | Adding or updating tests                      |
| `build`    | patch        | Build system or dependency changes            |
| `ci`       | patch        | CI configuration changes                      |
| `chore`    | patch        | Other maintenance changes                     |
| `revert`   | patch        | Reverts a previous commit                     |

### Breaking Changes

To trigger a **major** version bump, add `!` after the type:

```
feat!: redesign configuration API
```

Or include a `BREAKING CHANGE:` footer in the commit message body.

### Version Bump Rules

| Change type | Bump  | Example       |
|-------------|-------|---------------|
| `fix: ...`  | patch | 0.1.0 → 0.1.1 |
| `feat: ...` | minor | 0.1.0 → 0.2.0 |
| `feat!:`    | major | 0.1.0 → 1.0.0 |

On **major** bump: minor and patch reset to 0.
On **minor** bump: patch resets to 0.

### Examples

```
fix: handle null pointer in task runner      → patch
feat: add dark mode toggle                   → minor
feat!: change config file format             → major
docs: update installation guide              → patch
chore(deps): bump textual to 8.3.0           → patch
```

---

## CI Checks (`.github/workflows/ci.yml`)

Runs on every pull request targeting `main`. All checks must pass before
the PR can be merged.

### What is checked

1. **Unit tests and BDD tests** — `poetry run pytest`
   - All tests must pass
   - Runs in parallel by default (`-n auto`)

2. **Type checking** — `poetry run mypy src/`
   - Strict mode enabled
   - No type errors allowed

3. **Unused imports** — `poetry run autoflake --remove-all-unused-imports --ignore-init-module-imports --check --recursive src/`
   - No unused imports in the source code

4. **Changelog not empty** — custom bash check
   - The `[Unreleased]` section in `CHANGELOG.md` must contain at least one entry
   - This ensures every merged change is documented

### How to add changelog entries

In your PR, add entries under the appropriate subsection in `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- New task scheduling feature

### Fixed
- Crash when config file is missing
```

Valid subsections: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

---

## PR Title Validation (`.github/workflows/pr-title.yml`)

Runs on every PR targeting `main`. Uses
[action-semantic-pull-request](https://github.com/amannn/action-semantic-pull-request).

The PR title determines the version bump type when merged. With squash merge,
the PR title becomes the commit message on `main`.

### Format

```
<type>(<optional scope>): <description>
```

Must start with one of: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`,
`test`, `build`, `ci`, `chore`, `revert`.

---

## Release Workflow (`.github/workflows/release.yml`)

Triggers automatically when a commit is pushed to `main` (i.e., when a PR
is merged). Skips commits made by the release bot itself to prevent loops.

### What it does

1. **Determines version bump** from the commit message (squashed PR title)
2. **Calculates new version** from current version in `pyproject.toml`
3. **Updates `pyproject.toml`** via `poetry version <new-version>`
4. **Updates `CHANGELOG.md`**:
   - Moves `[Unreleased]` content under a new `## [<version>] - <date>` heading
   - Re-adds an empty `[Unreleased]` section for future entries
5. **Commits** the changes as `chore(release): <version>`
6. **Creates a git tag** (format: `<version>`, e.g., `1.0.0` — no `v` prefix)
7. **Pushes** the commit and tag to `main`
8. **Creates a GitHub Release** with auto-generated release notes

### Tag format

Tags use **bare semver** without a `v` prefix:

```
1.0.0
0.2.3
```

### Permissions

The workflow requires `contents: write` permission to push commits and
create tags/releases. This is granted via the default `GITHUB_TOKEN`.

---

## Branch Protection (Optional — Not Yet Enabled)

Branch protection rules can be configured on `main` to enforce the CI
checks as merge requirements. This is **not currently enabled** but
can be activated via the GitHub UI or CLI when ready.

### What it enforces (when enabled)

- **Require pull request** — no direct pushes to `main`
- **Require status checks** — `ci` and `pr-title` must pass
- **Require branches to be up to date** — PRs must be based on latest `main`
- **Squash merge only** — only squash merge is allowed

### Enabling via CLI

```bash
# Protect main branch
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci","pr-title"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":0}' \
  --field restrictions=null

# Restrict merge strategy to squash only (repo settings)
gh api repos/{owner}/{repo} \
  --method PATCH \
  --field allow_merge_commit=false \
  --field allow_rebase_merge=false \
  --field allow_squash_merge=true
```

### Enabling via GitHub UI

1. Go to **Settings → Branches**
2. Click **Add rule** next to "Branch protection rules"
3. Branch name pattern: `main`
4. Check **Require a pull request before merging**
5. Check **Require status checks to pass**
6. Search and select: `ci`, `pr-title`
7. Check **Require branches to be up to date before merging**
8. Under **Rules applied to everyone**, check **Do not allow bypassing the above settings**
9. Click **Create**

---

## Complete Developer Workflow

1. Create a feature branch from `main`
2. Make changes and commit with conventional commit messages
3. **Add a changelog entry** under `## [Unreleased]` in `CHANGELOG.md`
4. Open a PR to `main` with a conventional commit title (e.g., `feat: add task history`)
5. CI automatically runs all checks
6. Fix any failures until all checks are green
7. Merge via **squash merge** → release is automatic

---

## Troubleshooting

### "CHANGELOG.md [Unreleased] section is empty"
Add at least one entry under `## [Unreleased]` in your PR.

### "PR title does not match Conventional Commits"
Rename your PR to follow the format: `type: description` (e.g., `fix: resolve crash`).

### Release workflow did not trigger
Ensure the PR was merged (not closed without merge). The workflow only
triggers on push to `main`.

### Version was not bumped
Check the commit message on `main` — it must follow conventional commits
format. A `chore:` commit (from the release bot itself) is intentionally skipped.
