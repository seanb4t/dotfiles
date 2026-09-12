# respond-to-pr-comments Design Document

## Goals

Provide minimal-token operations for viewing and managing GitHub PR review
comments and feedback.

### Primary Operations

1. **List comments** - Show all or unacknowledged comments on a PR
2. **Get comment** - Retrieve specific comment details with optional file save
3. **Get latest** - Find most recent comment
4. **Acknowledge** - Mark comment as reviewed with thumbs-up reaction
5. **Comment** - Add response to PR

### Design Principles

1. **Minimal tokens** - Markdown output instead of JSON (~40% reduction)
2. **No workflows** - Provide tools only, no mandatory processes
3. **File-based I/O** - Avoid heredoc complications for multi-line content
4. **Ack tracking** - Use GitHub reactions API to track processed comments
5. **Clear IDs** - Prefixed format (`RC_*`/`R_*`) indicates comment type

## Architecture

### Single Script

`scripts/pr_comments` - All operations in one executable

**Commands:**

- `list <pr> [--unacked]` - List with optional filtering
- `get <pr> <id> [--save <path>]` - Retrieve with optional save
- `latest <pr>` - Most recent comment
- `ack <pr> <id>` - Add thumbs-up reaction
- `comment <pr> {text | --file <path>}` - Add comment

### Output Format

Markdown structure:

```markdown
## [✓] RC_123456 - @username

**File:** path/to/file.ts:42

Comment body text here...

*Ack:* `pr_comments ack 123 RC_123456`
```

Minimal, scannable, pipeable to grep/awk/sed.

### Acknowledgment Tracking

Uses GitHub reactions API:

1. Check if authenticated user has +1 reaction on comment
2. Display `[✓]` (acked) or `[○]` (unacked) in output
3. Filter with `--unacked` flag
4. Add reaction with `ack` command

## Non-Goals

### Removed from Original Design

1. **Action item parsing** - No severity classification (blocking/important/suggestion)
2. **Mandatory workflows** - No required delegation to sub-agents
3. **Auto-processing** - No automatic commit/push/PR comment patterns
4. **Complete text emphasis** - Trust users can handle truncation if needed
5. **Grep functionality** - Standard `grep` works fine on markdown output

### Why These Were Removed

- **Overengineering** - 297 lines of workflow for 5 operations
- **Token waste** - JSON + verbose instructions consumed context
- **Hidden complexity** - "Action item" focus masked simple comment operations
- **Scope creep** - Became PR feedback processor vs. comment viewer

## Usage Patterns

### View unacknowledged feedback

```bash
pr_comments list 123 --unacked | less
```

### Get specific comment for editing

```bash
pr_comments get 123 RC_456 --save /tmp/comment.md
# Edit file, then reply
pr_comments comment 123 --file /tmp/reply.md
pr_comments ack 123 RC_456
```

### Check latest activity

```bash
pr_comments latest 123
```

### Search for specific topic

```bash
pr_comments list 123 | grep -i "authentication"
```

## Future Considerations

### Potential Additions

- **Multi-PR listing** - Search comments across PRs (if GitHub API supports efficiently)
- **Author filtering** - `--author <username>` flag
- **Time filtering** - `--since <date>` or `--last-24h`

### Not Recommended

- **Built-in grep** - Pipe to `grep` is simpler
- **Severity classification** - Adds complexity without clear benefit
- **Workflow automation** - Let users/Claude decide how to process

## Migration Notes

### From Old Design

Old design required:

1. `fetch_pr_comments` - Fetch all comment data to JSON
2. `parse_action_items.py` - Parse and classify into severity levels
3. Follow 10-step workflow with mandatory TodoWrite tracking

New design:

1. Single `pr_comments` with 5 commands
2. Markdown output, optional file I/O
3. No mandatory patterns

### Breaking Changes

- Script names changed
- Output format changed (JSON → Markdown)
- No action item/severity JSON output
- No workflow enforcement

## Implementation Details

### Comment ID Format

- `RC_{numeric_id}` - Review comment (inline code comment)
- `R_{numeric_id}` - Review (with body text)

Numeric ID extracted from GitHub API response, prefixed for user clarity.

### Acknowledgment via Reactions

GitHub API endpoints:

- Review comments: `repos/{owner}/{repo}/pulls/comments/{id}/reactions`
- Reviews: `repos/{owner}/{repo}/pulls/{pr}/reviews/{id}/reactions`

Check for `+1` reaction from authenticated user (via `gh api user`).

### Error Handling

- Comment not found: Clear error message with comment ID
- Missing flags: Usage help with examples
- API failures: Pass through `gh` CLI error messages

## Performance

### Token Usage

- Old design: ~1500 tokens for 10 comments (JSON + instructions)
- New design: ~600 tokens for 10 comments (Markdown)
- **60% reduction**

### API Calls

Per operation:

- `list`: 1 call (`gh pr view --json`)
- `get`: 1 call + 1 reaction check
- `latest`: 1 call
- `ack`: 1 call (POST reaction)
- `comment`: 1 call

No unnecessary prefetching or caching.
