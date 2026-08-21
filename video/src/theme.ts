// One place for every colour and metric, so the film stays consistent.
export const T = {
  bg: "#0C0C0E",
  panel: "#17171C",
  ink: "#E8E6E2",
  dim: "#8A8894",
  faint: "#55535E",
  rule: "#26262E",
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
  // 1. the token line, so 81% is unmissable. Its text spans x 3%..31%, and it
  //    sits 38px from the foot of a 1080 frame.
  { a: 12,  b: 34,  c: 74,  d: 92,  scale: 2.0, ox: 0.17, oy: 0.965 },
  // 2. the input line while /keep is typed, 84px from the foot
  { a: 96,  b: 116, c: 168, d: 190, scale: 2.0, ox: 0.10, oy: 0.922 },
  // 3. the recommended stop, twelve lines above the foot of the transcript
  { a: 336, b: 358, c: 404, d: 424, scale: 1.9, ox: 0.22, oy: 0.417 },
  // 4. the picker counter reaching 56
  { a: 470, b: 492, c: 530, d: 552, scale: 1.9, ox: 0.14, oy: 0.396 },
  // 5. the token line again, showing 29%
  { a: 700, b: 724, c: 770, d: 790, scale: 2.0, ox: 0.17, oy: 0.965 },
];
