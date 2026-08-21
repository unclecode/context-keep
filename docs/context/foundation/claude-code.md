---
title: What Claude Code provides
status: foundational
sources:
  - external:claude-code-2.1.237
  - .claude/skills/keep-context/fragments.config
related:
  - foundation/session-files.md
  - reference/keep-command.md
---

# What Claude Code provides

This project does not summarize anything and does not write to a session file. Claude Code
already does both. These are the facts it relies on, read from the shipped binary of
version **2.1.237**.

> **Never edit a session JSONL.** The summarize step is native. Editing the file risks
> corrupting a running session for no gain.

## The Rewind picker already summarizes a prefix

Esc twice opens the message selector. After choosing a message the menu offers six options:

```
Restore code and conversation
Restore conversation
Restore code
Summarize from here        + add context (optional)
Summarize up to here       + add context (optional)
Never mind
```

The handler takes an index and a direction:

```js
direction === "up_to" ? messages.slice(0, t) : messages.slice(t)   // summarized
                        messages.slice(t)                          // kept
```

So **"Summarize up to here"** summarizes everything before the selected message and keeps
the selected message and everything after it, word for word. That is exactly the operation
this project points at. Its failure text is
`"Nothing to summarize before the selected message."`.

The `add context (optional)` field becomes the focus note for the summary prompt. That is
where `FOCUS_TEXT` in `report.py` is meant to be pasted.

Claude Code has a prompt written for this case: *"This summary will be placed at the start
of a continuing session; newer messages that build on this context will follow after your
summary (you do not see them here)."* Its full compaction prompt has eight numbered
sections, including *Files and Code Sections* and *Errors and fixes*.

## What cannot be automated

There is no parameter, hook or flag that selects the message. `PreCompact` hooks can block
compaction, seen as `"Compaction blocked by PreCompact hook"`, and can return
`newCustomInstructions` which reach the summarizer. Neither carries a boundary index. So
`/keep` advises; the person acts.

## Other facts used

- `$CLAUDE_CODE_SESSION_ID` holds the current session id and is visible to a Bash command.
- Hooks receive `session_id` and `transcript_path` as JSON on stdin.
- `autoCompactEnabled` in `settings.json` turns auto-compaction off.
- `microcompact` drops old tool results and keeps a recent count. It writes no summary.
- Hook events present in 2.1.237, more than the docs list: `PreCompact`, `PostCompact`,
  `SessionStart`, `SessionEnd`, `StopFailure`, `SubagentStart`, `TaskCreated`,
  `TaskCompleted`, `MessageDisplay`, `FileChanged`, `CwdChanged`, `ConfigChange`,
  `InstructionsLoaded`, `UserPromptExpansion`, `PermissionRequest`, `PostToolBatch`,
  `WorktreeCreate`, `WorktreeRemove`, `TeammateIdle`.
- `hookSpecificOutput.additionalContext` is accepted for `UserPromptSubmit`, `PostToolUse`,
  `PostToolBatch` and `Stop`/`SubagentStop`. Not for `PreCompact`.

## The slash command

`~/.claude/commands/keep.md` is global and runs `keep.py` through the Bash tool, then asks
for the output back verbatim. An earlier version used the `` !`…` `` form, which sends the
output to the model as context and shows the user nothing.

## Key files

| File | Role |
|---|---|
| `~/.claude/commands/keep.md` | the global `/keep` command, outside this repo |
