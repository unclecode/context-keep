// One place for every colour and metric, so the film stays consistent.
export const T = {
  bg: "#0C0C0E",
  panel: "#17171C",
  ink: "#E8E6E2",
  dim: "#8A8894",
  faint: "#55535E",
  rule: "#26262E",
  focus: "#7C8CF8",   // the blue Claude Code puts on the focused box
  accent: "#B69BE0",     // the icon accent
  zone: "#DCA84A",
  good: "#6FBF95",
  warn: "#E08B69",
  chip: "#9FC6B4",
  mono: "'DejaVu Sans Mono', 'Menlo', monospace",
  fs: 28,                // terminal font size, sized for a phone
  lh: 40,                // line height
  padX: 64,
  inputH: 150,           // rule + prompt + status, measured from the bottom
};

export const FPS = 30;
export const DUR = 36 * FPS;   // 1080 frames

// Scene edges, in frames. 36 seconds.
export const S = {
  idle:      [0,   90],
  typing:    [90,  150],
  running:   [150, 186],
  printing:  [186, 330],
  zone:      [330, 432],   // the chart and the recommended stop
  picker:    [432, 546],   // the list scrolls until the counter reads 56
  hold56:    [546, 591],   // it stops there, painted, for a second and a half
  menu:      [591, 720],   // Enter, then Down four times, then Enter
  summarize: [720, 828],
  back:      [828, 960],
  card:      [960, 1080],
} as const;

// Zoom moves. Each is [start, hold-in, hold-out, end, scale, originX, originY].
// originX and originY are fractions of the frame, so 0.5,0.5 is the middle.
export const ZOOMS: Array<{
  a: number; b: number; c: number; d: number;
  scale: number; ox: number; oy: number;
  // A move may drift to a second target between frames m1 and m2, so the
  // camera follows the action instead of cutting to it.
  m1?: number; m2?: number; scale2?: number; ox2?: number; oy2?: number;
}> = [
  // 1. the foot: the input line and the token count, held while /keep is typed
  { a: 14,  b: 44,  c: 168, d: 196, scale: 1.9, ox: 0.15, oy: 0.945 },
  // 2. the chart, the step up and the recommended stop
  { a: 336, b: 372, c: 414, d: 438, scale: 1.7, ox: 0.28, oy: 0.440 },
  // 3. the picker counter, held on 56, then through the whole menu, and out
  //    only after Summarizing appears
  { a: 500, b: 536, c: 744, d: 780, scale: 1.7, ox: 0.16, oy: 0.845,
    m1: 585, m2: 625, scale2: 1.5, ox2: 0.19, oy2: 0.760 },
  // 4. the token count again, showing 29%
  { a: 862, b: 898, c: 930, d: 954, scale: 2.0, ox: 0.17, oy: 0.965 },
];

/** Captions. Each is one short line, shown while the shot behind it runs. */
export const CAPTIONS: Array<{ a: number; b: number; text: string; top?: boolean }> = [
  { a: 236, b: 300, text: "Every point is one place to stop." },
  { a: 306, b: 366, text: "The line jumps where new work starts.", top: true },
  { a: 372, b: 424, text: "Zone 1 is safe. Nothing after it needs what came before.", top: true },
  { a: 432, b: 492, text: "So stop at message 56.", top: true },
  { a: 546, b: 606, text: "Same 56. This is the message.", top: true },
  { a: 880, b: 950, text: "810k down to 290k. Nothing needed was lost." },
];
