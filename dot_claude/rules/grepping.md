Use the native Grep tool or `rg` for text and symbol searches; use `sg` (ast-grep) for code
*structure* (balanced/nested shapes a text regex cannot express); use grep-family tools only
where rg is unavailable — e.g. remote hosts: prefer `ssh host 'producer' | rg 'pat'` so
filtering runs locally.

`rg` is **not** flag-compatible with `grep`: Rust regex (bare `|` alternation, no `\|`),
recursive by default, `.gitignore`-aware, hidden files skipped, multiline OFF.

The `rg-guard` PreToolUse hook (grepping plugin) denies the known-fatal grep habits and puts
the corrected command in the deny reason — apply that correction rather than improvising.
Prefix with `RG_GUARD_OK=1` only when the flagged behavior is deliberate.

If a search unexpectedly returns nothing, suspect filters before absence: retry with
`--no-ignore --hidden`, then `--debug`.

Load the `grepping:grepping` skill before writing an `rg` invocation into a script, test, CI
step, or acceptance gate (durable-gate checklist: prove it goes RED, count occurrences with
`-o | wc -l` not `-c`, prefer set-equality over exit-status chains), and when diagnosing a
surprising miss.
