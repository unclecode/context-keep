import React from "react";
import { T } from "./theme";

/** The bar mark from assets/icon, drawn inline so the film needs no files. */
export const Mark: React.FC<{ size: number }> = ({ size }) => {
  const xs = [6.0, 9.1, 12.8, 17.4, 23.3, 30.9, 41.0, 54.6];
  return (
    <svg width={size} height={size} viewBox="0 0 64 64">
      {xs.map((x, i) => (
        <rect key={i} x={x} y={14} width={3.4} height={36} rx={1.7}
              fill={i >= 5 ? T.accent : T.ink} />
      ))}
    </svg>
  );
};

/** One line of terminal text. */
export const Line: React.FC<{ text: string; color?: string; dim?: boolean }> =
  ({ text, color, dim }) => (
    <div style={{
      fontFamily: T.mono, fontSize: T.fs, lineHeight: `${T.lh}px`,
      color: color ?? (dim ? T.dim : T.ink), whiteSpace: "pre",
    }}>{text}</div>
  );

/**
 * The foot of the window, exactly as Claude Code draws it:
 * a hint line, a session chip, a rule, the prompt, then the token line.
 */
export const Foot: React.FC<{
  pct: number; typed: string; caret: boolean; hint?: string; chip: string;
}> = ({ pct, typed, caret, hint, chip }) => {
  const used = Math.round(pct * 10);          // 81% -> 810k of 1000k
  const barW = 150;
  return (
    <div style={{
      position: "absolute", left: T.padX, right: T.padX, bottom: 26,
      fontFamily: T.mono,
    }}>
      {hint && (
        <div style={{
          textAlign: "right", fontSize: T.fs - 4, color: T.dim, marginBottom: 6,
        }}>{hint}</div>
      )}
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
        <span style={{
          background: T.chip, color: "#10221C", fontSize: T.fs - 6,
          padding: "3px 12px", letterSpacing: 0.4,
        }}>{chip}</span>
      </div>
      <div style={{ height: 1, background: T.rule, marginBottom: 14 }} />
      <div style={{
        display: "flex", alignItems: "center", gap: 14,
        fontSize: T.fs, color: T.ink, marginBottom: 18,
      }}>
        <span style={{ color: T.dim }}>›</span>
        <span style={{ whiteSpace: "pre" }}>{typed}</span>
        <span style={{
          width: 15, height: T.fs + 6,
          background: caret ? T.ink : "transparent",
        }} />
      </div>
      <div style={{
        display: "flex", alignItems: "center", gap: 16,
        fontSize: T.fs - 5, color: T.dim,
      }}>
        <div style={{ width: barW, height: 3, background: "#23232B" }}>
          <div style={{
            width: (barW * pct) / 100, height: 3,
            background: pct > 70 ? T.warn : T.good,
          }} />
        </div>
        <span>{Math.round(pct)}% ({used}k/1000k) · think:on</span>
      </div>
    </div>
  );
};

/** The window frame everything sits inside. */
export const Shell: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ position: "absolute", inset: 0, background: T.bg }}>
    <div style={{
      position: "absolute", top: 0, left: 0, right: 0, height: 40,
      borderBottom: `1px solid ${T.rule}`,
    }} />
    {children}
  </div>
);

/**
 * The scroll area. Content is anchored to the BOTTOM and grows upward, the way
 * Claude Code does it: new output appears above the input line and pushes the
 * older lines off the top.
 */
export const Scroll: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{
    position: "absolute", top: 40, left: T.padX, right: T.padX,
    bottom: T.inputH, overflow: "hidden",
    display: "flex", flexDirection: "column", justifyContent: "flex-end",
  }}>
    {children}
  </div>
);
