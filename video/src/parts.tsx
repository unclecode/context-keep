import React from "react";
import { T } from "./theme";

/** The bar mark from assets/icon, drawn inline so the film needs no files. */
export const Mark: React.FC<{ size: number; opacity?: number }> = ({ size, opacity = 1 }) => {
  const xs = [6.0, 9.1, 12.8, 17.4, 23.3, 30.9, 41.0, 54.6];
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" style={{ opacity }}>
      {xs.map((x, i) => (
        <rect key={i} x={x} y={14} width={3.4} height={36} rx={1.7}
              fill={i >= 5 ? T.accent : T.ink} />
      ))}
    </svg>
  );
};

/** One line of terminal text, with the parts that need a colour picked out. */
export const Line: React.FC<{ text: string; color?: string; dim?: boolean }> =
  ({ text, color, dim }) => (
    <div style={{
      fontFamily: T.mono, fontSize: T.fs, lineHeight: `${T.lh}px`,
      color: color ?? (dim ? T.dim : T.ink), whiteSpace: "pre",
    }}>{text}</div>
  );

/** The status line at the foot of the window. */
export const StatusBar: React.FC<{ pct: number; label?: string }> = ({ pct, label }) => {
  const width = 260;
  const tone = pct > 70 ? T.warn : pct > 45 ? T.zone : T.good;
  return (
    <div style={{
      position: "absolute", left: T.padX, right: T.padX, bottom: 34,
      display: "flex", alignItems: "center", gap: 18,
      fontFamily: T.mono, fontSize: 18, color: T.dim,
    }}>
      <span style={{ color: T.faint }}>~/work/fetcher</span>
      <div style={{ flex: 1 }} />
      <span>{label ?? "context"}</span>
      <div style={{ width, height: 8, background: "#2A2A33", borderRadius: 4 }}>
        <div style={{
          width: (width * pct) / 100, height: 8, background: tone, borderRadius: 4,
        }} />
      </div>
      <span style={{ color: tone, width: 58, textAlign: "right" }}>{Math.round(pct)}%</span>
    </div>
  );
};

/** The window frame everything sits inside. */
export const Shell: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ position: "absolute", inset: 0, background: T.bg }}>
    <div style={{
      position: "absolute", top: 0, left: 0, right: 0, height: 46,
      display: "flex", alignItems: "center", paddingLeft: 22, gap: 9,
      borderBottom: `1px solid #24242C`,
    }}>
      {["#3A3A44", "#3A3A44", "#3A3A44"].map((c, i) => (
        <div key={i} style={{ width: 12, height: 12, borderRadius: 6, background: c }} />
      ))}
      <span style={{
        fontFamily: T.mono, fontSize: 16, color: T.faint, marginLeft: 16,
      }}>claude</span>
    </div>
    {children}
  </div>
);

export const Cursor: React.FC<{ on: boolean }> = ({ on }) => (
  <span style={{
    display: "inline-block", width: 11, height: 22, verticalAlign: "-4px",
    background: on ? T.ink : "transparent",
  }} />
);
