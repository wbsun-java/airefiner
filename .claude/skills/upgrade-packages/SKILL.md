---
name: upgrade-packages
description: Upgrades approved packages in requirements.txt to confirmed target versions, reinstalls into .venv, runs the test suite, and reports results. Invoke only after the user has approved specific package upgrades (e.g. from the upgrade-research agent output). Do not invoke for exploratory research — use upgrade-research for that.
effort: medium
allowed-tools: Read, Edit, Grep, Glob, Bash(pip *), Bash(.venv/bin/pip *), Bash(.venv/bin/python *), Bash(python *), Bash(pytest *), Bash(.venv/bin/pytest *), Bash(git *)
---

# Upgrading packages

Use this skill only after the user has approved specific package upgrades with target versions.

Arguments:
$ARGUMENTS

## Goal

Upgrade only the approved packages to the confirmed target versions, then validate the project with the smallest safe change set.

## This project

- **Dependency file:** `requirements.txt` — uses `>=VERSION` floor constraints, not pinned `==`
- **Virtual environment:** `.venv/` — must be kept in sync after any change
- **Test runner:** `.venv/bin/python -m pytest tests/`
- **No lock file** — `requirements.txt` is the single source of truth

## Workflow

### 1. Pre-flight checks

Verify the environment is ready before touching anything:

```bash
# Confirm .venv exists
ls .venv/bin/python

# Confirm test suite is currently passing (baseline)
.venv/bin/python -m pytest tests/ -q
```

If tests are already failing before the upgrade, stop and report — do not proceed. The user needs a green baseline first.

### 2. Record current state

Read `requirements.txt` and note the current version floor for every package you are about to upgrade.

### 3. Update `requirements.txt`

For each approved package, raise the floor constraint to the confirmed target version:

```
anthropic>=0.86.0   →   anthropic>=0.91.0
```

Only edit lines for packages that were explicitly approved. Do not touch anything else.

### 4. Reinstall into `.venv`

```bash
.venv/bin/pip install -r requirements.txt --upgrade
```

Capture the full output. If pip reports a conflict or error, stop and report it before continuing.

### 5. Verify installed versions

```bash
.venv/bin/pip show PACKAGE_NAME
```

Run for each upgraded package. Confirm the `Version:` field matches the target. If pip installed a different version (e.g. a transitive constraint forced a lower version), report it clearly.

### 6. Run the test suite

```bash
.venv/bin/python -m pytest tests/ -v
```

Do not suppress failures. If tests fail:
- Determine whether the failure is caused by the upgrade (API change, removed symbol, changed signature).
- If the fix is small and self-contained (renamed import, changed parameter name), apply it and re-run once.
- If the fix requires broad refactoring, **stop and report** — describe exactly what broke and why before asking the user how to proceed.

### 7. Report results

```
## Upgrade Results

| Package   | Old floor  | New floor  | Installed |
|-----------|------------|------------|-----------|
| anthropic | >=0.86.0   | >=0.91.0   | 0.91.0    |

**Files modified:**
- requirements.txt
- [any source files changed for compatibility fixes]

**Test result:** 65 passed / 0 failed

**Notes:** [compatibility fixes applied, version mismatches, or risks to watch]

**To revert:** git checkout requirements.txt && .venv/bin/pip install -r requirements.txt
```

Always include the revert command so the user knows how to undo.

## Safety rules

- Do not upgrade packages that were not explicitly approved.
- Do not switch the package manager or change the `.venv` layout.
- Do not invent version numbers — use only the versions provided.
- Do not suppress test failures with `--ignore`, `-k`, or `--no-header`.
- Do not proceed if the baseline test run fails.
- If the target version is missing or ambiguous, ask for confirmation before editing any file.
