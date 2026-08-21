// Every line of conversation here is invented. Only the tool's own output,
// the chart and the numbers, comes from a real run.

export const HISTORY = [
  ["user", "ok now wire the retry into the fetch path, keep the backoff"],
  ["claude", "Done. fetch.rs:212 now retries three times with the same backoff."],
  ["user", "why did the second attempt fire after 40ms and not 400?"],
  ["claude", "The multiplier was applied before the first sleep, not after."],
  ["user", "fix it, dont commit, I read the diff"],
  ["claude", "Fixed at fetch.rs:220. Nothing committed."],
  ["user", "good. now the cache layer, same treatment"],
];

export const REPORT = [
  "  keep  session 8f31c04a · 188 messages · 112 places to stop",
  "",
  "  self-containment",
  "  0.66 ┤                                         ▃▇█▇▇▆▆▅▆▆▆▇▇",
  "  0.63 ┤                                        ▅│            ",
  "  0.60 ┤                                        │             ",
  "  0.57 ┤                                       ▃│             ",
  "  0.54 ┤▁▁▂▁▁▁▁                        ▁▁      │              ",
  "  0.51 ┤       ▇▆▅▃▂▁▁                ▄│ ▃▄▂▂▁▂│              ",
  "  0.48 ┤              ▇▇▇▆▆▇▆▄▂▁▁▁▁ ▃▇│                       ",
  "       └──────────────────────────────────────────────────────",
  "        ·······································▔▔▔ zone 1 ▔▔▔▔",
  "        older → newer",
  "",
  "  zone 1  keeps 0.50  a clear break, 191x the noise",
  "    stop here     below~56  \"ok good we got the plan settled\"",
  "    anything newer is as safe, and saves more",
  "",
  "  zone 2  keeps 0.49  a clear break, 46x the noise",
  "    stop here     below~76  \"ok, back to the cache layer now\"",
  "    anything newer is as safe, and saves more",
  "",
  "  How to use it",
  "    1. Press Esc twice.",
  "    2. Go up until the list shows “↓ 56 more below”.",
  "    3. Choose “Summarize up to here”.",
  "    4. Paste this into the context box:",
];

export const PICKER = [
  "ok now wire the retry into the fetch path, keep the backoff",
  "why did the second attempt fire after 40ms and not 400?",
  "fix it, dont commit, I read the diff",
  "good. now the cache layer, same treatment",
  "(current)",
];

export const MENU = [
  "Restore code and conversation",
  "Restore conversation",
  "Restore code",
  "Summarize from here",
  "Summarize up to here",
  "Never mind",
];

export const NOTE =
  "Keep exact: file names, line numbers, flag and field names, and the " +
  "decision behind each one.";
