// One place for every colour and metric, so the film stays consistent.
export const T = {
  bg: "#16161A",
  panel: "#1C1C22",
  ink: "#E6E4E0",
  dim: "#8A8894",
  faint: "#4A4854",
  accent: "#B69BE0",     // the icon accent
  zone: "#DCA84A",
  good: "#6FBF95",
  warn: "#E08B69",
  mono: "'DejaVu Sans Mono', 'Menlo', monospace",
  fs: 17,                // terminal font size
  lh: 24,                // line height
  padX: 54,
};

export const FPS = 30;
export const DUR = 24 * FPS;   // 720 frames

// Scene edges, in frames.
export const S = {
  idle:      [0,   75],
  typing:    [75,  120],
  running:   [120, 150],
  printing:  [150, 270],
  zoom:      [270, 345],
  picker:    [345, 420],
  menu:      [420, 495],
  summarize: [495, 570],
  back:      [570, 660],
  card:      [660, 720],
} as const;
