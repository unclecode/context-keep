# context-keep

Finds where a long Claude Code chat can be summarized. Claude Code does the summarizing
itself, through "Summarize up to here" in the Rewind picker. This project only says where.

## Words

- A **stop** is where the kept part starts. Never call it a cut: nothing is deleted.
- **Self-containment** is the measure. **Safe zone** is the answer it produces.

## Docs

Design docs are fragments under `docs/context/`, one per subsystem, each declaring the
files it covers. Load the right one with `/keep-context`.

Before pushing, run `/keep-context sync`: map changed sources to fragments, update
them, approve, and commit the docs with the code.
