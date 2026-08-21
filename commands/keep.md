---
description: Find where this chat can be summarized, and what to keep word for word
argument-hint: "[--html] [--top N]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/keep.py"*)
---

Run this command:

```
python3 "${CLAUDE_PLUGIN_ROOT}/keep.py" $ARGUMENTS
```

Then print its output back exactly as it is, inside a plain code block.
Add no commentary, no summary, no extra words.
