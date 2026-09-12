---
name: jj-init
description: >-
  Initialize a colocated jj repo in an existing git repository.
  Use when the user asks to "set up jj", "init jj", or "colocate jj".
user-invocable: true
allowed-tools:
  - "Bash(jj *)"
  - "Bash(git *)"
  - "Bash(test *)"
  - "Bash(grep *)"
  - "Bash(echo *)"
  - Read
  - Edit
  - Write
---

# Initialize Colocated jj Repo

## Steps

1. **Check prerequisites** — First, run `command -v jj` to confirm jj is installed. If not found,
   tell the user to install jj (<https://jj-vcs.github.io/jj/latest/install-and-setup/>) and stop.
   Then run `git rev-parse --show-toplevel` to confirm this is a git repository. If not, tell the
   user to run `git init` first or use `jj git init` for a standalone (non-colocated) repo.

2. **Check if already initialized** — Run `test -d .jj`. If the directory exists, tell the user
   "This repo already has jj initialized." and stop.

3. **Initialize colocated repo** — Run:

   ```bash
   jj git init --colocate
   ```

   The `--colocate` flag ensures jj shares the working copy with git.
   Always use `--colocate` when initializing in an existing git repo.

   **If the command fails**, report the full error output (stdout and stderr)
   to the user and stop. Include jj's error text so the user can diagnose the
   failure (e.g., unsupported flags, filesystem issues, already-initialized state).
   Do NOT proceed to modify `.gitignore` or run verification steps.

4. **Add .jj/ to .gitignore** — Check whether `.gitignore` exists and already contains `.jj/`.
   If not present, append `.jj/` to `.gitignore`:

   ```bash
   # 2>/dev/null: treat unreadable/missing .gitignore the same (append below will report real errors)
   grep -qxF '.jj/' .gitignore 2>/dev/null || {
     if ! append_err=$({ echo '.jj/' >> .gitignore; } 2>&1); then
       echo "Could not update .gitignore: ${append_err:-permission denied}" >&2
       echo "Could not update .gitignore: ${append_err:-permission denied}"
     fi
   }
   ```

   If the append fails, capture and surface the error as: "Could not update `.gitignore`:
   \<error text\>. Please add `.jj/` to `.gitignore` manually to prevent jj internals from
   being tracked by git."

5. **Verify** — Run `jj st` and `jj log --no-graph -n 3` to confirm the repo is working.
   Report success: "Colocated jj repo initialized. Both `jj` and `git` commands work in this
   directory."

   If step 4's `.gitignore` append failed, append this note to the success message:

   > NOTE: `.jj/` was not added to `.gitignore` (see error above). Add it manually to prevent
   > jj internals from being tracked by git.

   If `jj st` or `jj log` fails, report this as a potential init failure:
   "WARNING: jj git init --colocate may have failed — jj status check returned
   an error: \<error\>. Run `jj st` manually to verify." Do NOT report success.
