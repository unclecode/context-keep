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
export const DUR = 30 * FPS;   // 900 frames

// Scene edges, in frames. 30 seconds.
export const S = {
  idle:      [0,   90],
  typing:    [90,  150],
  running:   [150, 186],
  printing:  [186, 330],
  zoom:      [330, 420],
  picker:    [420, 510],
  menu:      [510, 600],
  summarize: [600, 690],
  back:      [690, 795],
  card:      [795, 900],
} as const;

// Zoom moves. Each is [start, hold-in, hold-out, end, scale, originX, originY].
// originX and originY are fractions of the frame, so 0.5,0.5 is the middle.
export const ZOOMS: Array<{
  a: number; b: number; c: number; d: number;
  scale: number; ox: number; oy: number;
}> = [
  // 1. the foot of the window: the input line and the token count together,
  //    held while /keep is typed
  { a: 14,  b: 44,  c: 168, d: 196, scale: 1.9, ox: 0.15, oy: 0.945 },
  // 2. the recommended stop
  { a: 336, b: 366, c: 404, d: 428, scale: 1.9, ox: 0.22, oy: 0.417 },
  // 3. the picker counter reaching 56
  { a: 468, b: 496, c: 532, d: 556, scale: 1.7, ox: 0.16, oy: 0.845 },
  // 4. the token count again, showing 29%
  { a: 700, b: 730, c: 768, d: 792, scale: 2.0, ox: 0.17, oy: 0.965 },
];
