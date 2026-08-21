import { Composition, registerRoot } from "remotion";
import React from "react";
import { Demo } from "./Demo";
import { FPS, DUR } from "./theme";

const Root: React.FC = () =>
  React.createElement(Composition, {
    id: "Demo", component: Demo, durationInFrames: DUR,
    fps: FPS, width: 1920, height: 1080,
  });

registerRoot(Root);
