---
title: Reading a Claude Code session file
status: foundational
sources:
  - context_keep/extract.py
related:
  - foundation/claude-code.md
  - foundation/self-containment.md
---

# Reading a Claude Code session file

Turns one session JSONL into the two lists everything else needs: the user's real
messages, and the entries the Rewind picker shows.

> **Pick the right branch or every number is wrong.** A rewind starts a new branch and
> leaves the old one in the file. A session rewound this morning can hold four messages on
> its live branch while the conversation it replaced sits complete beside it.

## Data model

`Timeline` holds three lists:

- `messages` — `UserMessage` records in order. Fields: `index` (1-based), `timestamp`,
  `text`, `is_compact`, `line_number`, `is_command`, `uuid`.
- `tool_uses` — `ToolUse` records with `after_user_index`, `name`, `file_path`, and
  `command` (filled for Bash only).
- `rewind_entries` — the uuids the Rewind picker lists, oldest first.

`is_compact` is true when the text starts with `COMPACT_PREFIX`,
`"This session is being continued from a previous conversation"`. Those messages are
summaries of earlier context, not user input, so scoring excludes them.

`is_command` is true for a slash command. `load_timeline` rewrites its text to just the
command name, for example `/model`, and keeps the record, because the picker lists it and
it therefore shifts every position count.

## Behavior

`load_timeline(path, branch="active")` runs in two passes.

**Pass one, per line.** Most lines are tool output that nothing here reads, so the line is
not parsed as JSON unless it is needed. Instead:

- `_SIDECHAIN` skips subagent lines.
- `_KIND` reads `"type"`. A `file-history-snapshot` line contributes its `_MESSAGE_ID` to
  the picker list and is then skipped, because it carries no uuid of its own.
- `_UUID_LINK` reads `uuid` and `parentUuid`. The two fields appear in either order, so the
  pattern has two arms and the caller picks the matching group pair.
- Only `user` and `assistant` lines are then parsed with `json.loads`.

This is why an 89MB session loads in 0.28s instead of 0.41s.

**Branch selection.** `branch` takes three values:

- `"active"` — `_active_branch` walks parents from the last line. This is the live
  conversation, and it is what a running session shows.
- `"longest"` — `_longest_branch` scores every node by how many **real** user messages sit
  on its chain, then takes the chain of the best leaf. Counting must skip tool results,
  because a `type: "user"` record is often a tool result and a branch full of them would
  win on volume alone. Use this to read a session that was rewound after the work was done.
- `"all"` — no filter. Used by `bench.py` to replay a past choice.

**Pass two, per kept line.** A user message is dropped when its text is empty, when it
starts with one of `SKIP_PREFIXES`, or when it exactly repeats the previous kept message,
which happens when a model switch resends the same prompt.

`SKIP_PREFIXES` covers command wrappers, tool notifications, system reminders, interrupt
markers, and two forms that Claude Code injects on the user's behalf:
`"(Re-invocation of"` and `"Base directory for this skill"`. Those two are skill bodies.
They arrive as ordinary user messages and dump hundreds of words at one point, which bends
the self-containment curve badly. See the RCA in `foundation/self-containment.md`.

Finally `rewind_entries` keeps the snapshot ids that are on the chosen branch, in file
order, with duplicates removed.

## Finding a transcript

**A compaction cuts the parent chain.** The boundary record has
`"parentUuid": null`, so walking back from the newest message stops there and
finds only the messages since the newest compaction. The picker shows many
more, because a compaction keeps some messages word for word and names them in
`compactMetadata.preservedMessages.uuids`. `branch="conversation"` takes the
chain from the newest message plus those uuids, which is exactly what the
picker lists. Verified against two real pickers: 159 entries and 61 entries,
both exact.

Taking every record after the boundary instead is wrong: a fork writes its
messages into the same file, and they would be pulled in.

The picker also skips anything the user did not type. Newer records carry
`origin.kind`, seen as `human`, `task-notification` and `auto-continuation`,
and a record with `stackedExpansion` is a command body, never listed. Older
records have no `origin` field and count as typed.

**The report reads the conversation branch.** The Rewind picker can select
nothing else, so a stop taken from another branch sends the reader looking for
a message that will never appear in the list. When the active branch is too
short to summarize, the report says so and prints the `--branch longest`
command rather than quietly reading the branch the user rewound away from.

`keep.session_path` reads `$CLAUDE_CODE_SESSION_ID`, then searches
`~/.claude/projects/*/<id>.jsonl`. It does not build the path from the current directory:
the project folder is named after the directory Claude Code **started in**, and a Bash tool
call can be running anywhere else. Hooks get `transcript_path` directly and need no search.

## Key files

| File | Role |
|---|---|
| `context_keep/extract.py` | parsing, branch selection, message filtering |
| `keep.py` | `session_path`, which locates the file |
