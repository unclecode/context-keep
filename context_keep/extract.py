"""Read a Claude Code session JSONL file into a simple timeline.

The timeline has two event kinds:
- UserMessage: one real text message the user typed.
- ToolUse: one tool call the assistant made (file path or bash command).
"""

import json
import re
from dataclasses import dataclass, field


# Wrapper lines that are not real user messages.
SKIP_PREFIXES = (
    "<local-command-caveat",
    "<command-name",
    "<command-message",
    "<local-command-stdout",
    "<task-notification",
    "<system-reminder",
    "[Request interrupted",
    "Caveat:",
    "(Re-invocation of",          # a skill reloading itself
    "Base directory for this skill",
)

COMPACT_PREFIX = "This session is being continued from a previous conversation"

# Field readers used to skip full JSON parsing on lines nothing reads.
_UUID_LINK = re.compile(r'"uuid":"([^"]+)".*?"parentUuid":(null|"[^"]*")|'
                        r'"parentUuid":(null|"[^"]*").*?"uuid":"([^"]+)"')
_SIDECHAIN = re.compile(r'"isSidechain":true')
_KIND = re.compile(r'"type":"([a-z-]+)"')
_MESSAGE_ID = re.compile(r'"messageId":"([^"]+)"')


@dataclass
class UserMessage:
    index: int            # 1-based position among kept user messages
    timestamp: str        # ISO string from the file
    text: str
    is_compact: bool      # True for an auto-compact summary message
    line_number: int
    is_command: bool = False  # True for a slash command entry like /model
    uuid: str = ""


@dataclass
class ToolUse:
    after_user_index: int  # index of the last user message before this call
    name: str              # tool name, e.g. Bash, Edit
    file_path: str         # file the call touched, empty if none
    command: str           # bash command text, empty if not Bash


@dataclass
class Timeline:
    path: str
    messages: list = field(default_factory=list)   # list[UserMessage]
    tool_uses: list = field(default_factory=list)  # list[ToolUse]
    # The prompts the Rewind picker lists, oldest first. These are the
    # file-history-snapshot records on the active branch, one per prompt.
    rewind_entries: list = field(default_factory=list)  # list[uuid]


def _text_of(content):
    """Return the plain text of a message content value, or empty."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        return " ".join(p for p in parts if p)
    return ""


def _chain_from(records, leaf):
    """The set of uuids from one message back to the root."""
    chain = set()
    uuid = leaf
    while uuid is not None and uuid not in chain:
        chain.add(uuid)
        uuid = records.get(uuid)
    return chain


def _active_branch(records, order):
    """The chain that ends at the newest message.

    A rewind leaves the abandoned messages in the file. Every line points to
    its parent with parentUuid, so the live conversation is the chain from
    the newest message back to the root.
    """
    return _chain_from(records, order[-1]) if order else None


def _longest_branch(records, order, is_message):
    """The chain that holds the most real user messages.

    After a rewind the live branch can be a few messages long while the
    conversation it replaced is still complete in the file. For a benchmark
    that older branch is the real conversation, so it wins.
    Counting must skip tool results: they are stored as user records too,
    and a branch full of them would win on volume alone.
    """
    if not order:
        return None
    best = {}
    for uuid in order:
        stack = []
        cur = uuid
        while cur is not None and cur not in best:
            stack.append(cur)
            cur = records.get(cur)
        count = best.get(cur, 0)
        for node in reversed(stack):
            count += 1 if is_message(node) else 0
            best[node] = count
    return _chain_from(records, max(order, key=lambda u: best[u]))


def load_timeline(path, branch="active"):
    """Parse one session JSONL file.

    branch="active" keeps only the live conversation: the parent chain from
    the newest message.
    branch="longest" keeps the chain with the most user messages. After a
    rewind that is the conversation the live branch replaced. Use it to read
    a session that was rewound after the work was done.
    branch="all" keeps every message in the file, including abandoned
    rewind branches. Use it to replay past choices.

    Steps:
    1. Read the file line by line; skip lines that are not valid JSON.
    2. Build the parent links; for branch="active" keep only the active
       branch (see _active_branch).
    3. Keep user messages that carry real text; drop command wrappers,
       tool results, and subagent (sidechain) lines.
    4. Drop an exact repeat of the previous kept message (model-switch resend).
    5. Record every assistant tool call with the file or command it touched.
    """
    raw = []
    records = {}   # uuid -> parentUuid
    order = []     # uuids in file order
    snapshot_ids = []
    for line_number, line in enumerate(open(path, encoding="utf-8"), 1):
        # Most lines are tool output that this file never reads. Parsing them
        # as JSON costs most of the run time, so pull the two link fields with
        # a regex and parse only the lines whose content is needed.
        if _SIDECHAIN.search(line):
            continue
        kind = _KIND.search(line)
        kind = kind.group(1) if kind else ""

        # A snapshot line carries no uuid of its own, only the id of the
        # prompt it belongs to.
        if kind == "file-history-snapshot":
            mid = _MESSAGE_ID.search(line)
            if mid:
                snapshot_ids.append(mid.group(1))
            continue

        m = _UUID_LINK.search(line)
        if m is None:
            continue
        # The two fields appear in either order, so the pattern has two arms.
        uuid, parent = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
        records[uuid] = None if parent == "null" else parent.strip('"')
        order.append(uuid)

        if kind in ("user", "assistant"):
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(obj, dict):
                raw.append((line_number, obj))

    if branch == "active":
        chain = _active_branch(records, order)
    elif branch == "longest":
        real = set()
        for _, obj in raw:
            text = _text_of((obj.get("message") or {}).get("content")).strip()
            if (obj.get("type") == "user" and text
                    and not text.startswith(SKIP_PREFIXES) and obj.get("uuid")):
                real.add(obj["uuid"])
        chain = _longest_branch(records, order, lambda u: u in real)
    else:
        chain = None

    tl = Timeline(path=path)
    last_text = None
    for line_number, obj in raw:
        if chain and obj.get("uuid") and obj["uuid"] not in chain:
            continue
        kind = obj.get("type")
        msg = obj.get("message") or {}

        if kind == "user":
            text = _text_of(msg.get("content")).strip()
            # A slash command shows in the Rewind list as its own entry
            # (for example "/model"), so keep it for position counting.
            cmd = re.search(r"<command-name>(/[\w:-]+)</command-name>", text[:300])
            if cmd:
                tl.messages.append(UserMessage(
                    index=len(tl.messages) + 1,
                    timestamp=obj.get("timestamp", ""),
                    text=cmd.group(1),
                    is_compact=False,
                    line_number=line_number,
                    is_command=True,
                    uuid=obj.get("uuid", ""),
                ))
                continue
            if not text or text.startswith(SKIP_PREFIXES):
                continue
            if text == last_text:
                continue
            last_text = text
            tl.messages.append(UserMessage(
                index=len(tl.messages) + 1,
                timestamp=obj.get("timestamp", ""),
                text=text,
                is_compact=text.startswith(COMPACT_PREFIX),
                line_number=line_number,
                uuid=obj.get("uuid", ""),
            ))

        elif kind == "assistant":
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not (isinstance(block, dict) and block.get("type") == "tool_use"):
                    continue
                inp = block.get("input") or {}
                tl.tool_uses.append(ToolUse(
                    after_user_index=len(tl.messages),
                    name=block.get("name", ""),
                    file_path=str(inp.get("file_path", "")),
                    command=str(inp.get("command", "")) if block.get("name") == "Bash" else "",
                ))

    seen = set()
    for mid in snapshot_ids:
        if mid and mid not in seen and (not chain or mid in chain):
            seen.add(mid)
            tl.rewind_entries.append(mid)
    return tl
