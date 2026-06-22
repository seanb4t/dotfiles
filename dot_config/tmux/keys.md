# tmux keys

**Prefix = `Ctrl+Space`** · **`M-` = left Option** (`macos-option-as-alt=left`).
"prefix o" = press `Ctrl+Space`, release, then `o`.

> Lost? `Ctrl+Space` then `Space` opens the **action menu** — every bind, pick or learn.

## Sessions (projects)

| Key | Action |
|-----|--------|
| `M-s` *(no prefix)* / `prefix o` | sesh picker — fuzzy jump or create a project session |
| `prefix w` | tree of all sessions + windows (zoomed, type to filter) |
| `prefix N` | new named session |
| `prefix d` | detach |

## Windows (tasks)

| Key | Action |
|-----|--------|
| `M-1` … `M-9` | jump to window N |
| `M-Tab` | last window (flip between two) |
| `M-[` / `M-]` | previous / next window |
| `prefix c` | new window (current dir) |
| `prefix b` | **jump to the next window needing attention** |

## Panes

| Key | Action |
|-----|--------|
| `M-h` `M-j` `M-k` `M-l` | move between panes (vim dirs, no prefix) |
| `prefix \|` / `prefix -` | split right / down |
| `prefix z` | zoom (fullscreen toggle) |
| `prefix q` | show pane numbers |
| `prefix x` | kill pane |
| `prefix H/J/K/L` | resize (hold to repeat) |

## Scratch popups

Floating overlays — they hover over your layout without disturbing your splits.

| Key | Action |
|-----|--------|
| `prefix g` | **scratch shell** — fresh shell in current dir, closes on exit |
| `prefix G` | **scratch session** — durable `scratch` session, survives closing the popup |

## Copy / grab

Copies land in the macOS clipboard automatically (`set-clipboard on` → OSC-52).

| Key | Action |
|-----|--------|
| scroll up / `prefix [` | enter scrollback / copy mode → `/` search · `v` select · `y` copy · `q` exit |
| drag-select | select with mouse; release copies (double-click = word, triple-click = line) |
| `Shift`+drag | bypass tmux → native Ghostty selection of the **visible** screen (then `Cmd+C`) |
| paste | `Cmd+V` (system clipboard) · `prefix ]` (tmux buffer) |
| `prefix F` | **fingers** — hint-labels on-screen tokens; type a letter to copy (`prefix J` = jump only) |
| `prefix Tab` | **extrakto** — fuzzy-pick text from pane / scrollback |

## Claude & housekeeping

| Key | Action |
|-----|--------|
| `Shift+Enter` | newline in Claude Code (not submit) |
| `Ctrl+V` | paste an **image** into Claude Code (`Cmd+V` = text) |
| `prefix m` | toggle mouse (default **on**: wheel scrolls into copy mode, drag selects) |
| `prefix Space` | action menu (discover everything) |
| `prefix ?` | this cheat-sheet |
| `prefix r` | reload config |

---

*Status bar:* `⚠ N` (left of the session name) = N windows awaiting you; clears when you visit them.
*Build muscle memory first on:* `M-s` (sessions) and `M-1..9` (windows) — they replace cmux's GUI.
