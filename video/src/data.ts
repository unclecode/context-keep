// Every line of conversation here is invented. Only the shape of the chart and
// the numbers come from the tool itself.

export const HISTORY: Array<[string, string]> = [
  ["user", "ok now wire the retry into the fetch path, keep the backoff"],
  ["claude", "Done. fetch.rs:212 now retries three times with the same backoff."],
  ["user", "why did the second attempt fire after 40ms and not 400?"],
  ["claude", "The multiplier was applied before the first sleep, not after."],
  ["user", "fix it, dont commit, I read the diff"],
  ["claude", "Fixed at fetch.rs:220. Nothing committed."],
  ["user", "good. now the cache layer, same treatment"],
];

/** The chart, drawn by the real renderer so the shape is honest. */
export const CHART = [
  "  0.70 ┤                                          ▃▅▅▇▆▅▇▆▇▇█▇",
  "  0.67 ┤▁▁                                        │           ",
  "  0.65 ┤  ▇▆▅▄▃▂▁                                ▂│           ",
  "  0.62 ┤         ▇▆▅▄▂▁▁                         │            ",
  "  0.59 ┤                ▇▆▅▄▃▂▁▁   ▁             │            ",
  "  0.56 ┤                        ▇▆▇│▆▂          ▂│            ",
  "  0.54 ┤                              ▇▄▃▂▁▁▁▁  │             ",
  "       └──────────────────────────────────────────────────────",
  "        ··········································▔ zone 1 ▔▔▔",
];

export const REPORT_HEAD = [
  "  keep  session 8f31c04a · 188 messages · 112 places to stop",
  "",
  "  self-containment",
];

export const REPORT_TAIL = [
  "        older → newer",
  "",
  "  zone 1  keeps 0.71  a clear break, 191x the noise",
  "    stop here     below~56  \"ok good we got the plan settled\"",
  "    anything newer is as safe, and saves more",
  "",
  "  zone 2  keeps 0.58  a sub-topic inside the same work, 12x the noise",
  "    stop here     below~76  \"ok, back to the cache layer now\"",
  "",
  "  How to use it",
  "    1. Press Esc twice.",
  "    2. Go up until the list shows “↓ 56 more below”.",
  "    3. Choose “Summarize up to here”.",
];

/** Rows in the Rewind picker. Each carries its own code-change note. */
export const PICKER: Array<{ text: string; changes: string }> = [
  { text: "why did the second attempt fire after 40ms and not 400?", changes: "No code changes" },
  { text: "fix it, dont commit, I read the diff", changes: "1 file changed" },
  { text: "ok good we got the plan settled", changes: "No code changes" },
  { text: "good. now the cache layer, same treatment", changes: "No code changes" },
  { text: "/keep", changes: "No code changes" },
];

export const SELECTED = 2;

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
