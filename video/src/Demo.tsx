import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { T, S } from "./theme";
import { HISTORY, REPORT, PICKER, MENU, NOTE } from "./data";
import { Mark, Line, StatusBar, Shell, Cursor } from "./parts";

const within = (f: number, [a, b]: readonly [number, number]) => f >= a && f < b;
const at = (f: number, [a, b]: readonly [number, number]) => (f - a) / (b - a);

/** Scene 1 to 4: the session, the command, the report printing. */
const Session: React.FC<{ f: number }> = ({ f }) => {
  const typed = within(f, S.typing)
    ? "/keep".slice(0, Math.floor(at(f, S.typing) * 6))
    : f >= S.typing[1] ? "/keep" : "";

  // The report prints line by line, and its chart draws column by column.
  const shown = f < S.printing[0] ? 0
    : Math.min(REPORT.length, Math.floor(at(f, S.printing) * REPORT.length * 1.25));
  const chartCols = f < S.printing[0] ? 0
    : Math.floor(interpolate(f, [S.printing[0] + 20, S.printing[0] + 70], [0, 60],
        { extrapolateRight: "clamp" }));

  const isChart = (i: number) => i >= 3 && i <= 12;

  return (
    <div style={{
      position: "absolute", top: 66, left: T.padX, right: T.padX, bottom: 78,
      overflow: "hidden",
    }}>
      <div>
      {HISTORY.map(([who, text], i) => (
        <div key={i} style={{ marginBottom: 4, opacity: 0.55 }}>
          <Line text={(who === "user" ? "› " : "● ") + text}
                color={who === "user" ? T.ink : T.dim} />
        </div>
      ))}
      <div style={{ height: 14 }} />
      <Line text={"› " + typed + (f < S.running[0] ? "" : "")} />
      {f >= S.running[0] && (
        <div style={{ marginTop: 10 }}>
          <Line text={f < S.printing[0] ? "  ✻ running…" : "  Ran 1 shell command"} dim />
        </div>
      )}
      {f >= S.printing[0] && (
        <div style={{ marginTop: 10 }}>
          {REPORT.slice(0, shown).map((l, i) => (
            <Line key={i}
                  text={isChart(i) ? l.slice(0, Math.max(0, chartCols + 7)) : l}
                  color={l.includes("zone 1") ? T.zone
                       : l.includes("below~56") ? T.accent : undefined}
                  dim={l.trim().startsWith("keep ") || l.includes("older →")} />
          ))}
        </div>
      )}
      </div>
    </div>
  );
};

/** Scene 5: the recommended stop grows out of the report. */
const Zoom: React.FC<{ f: number }> = ({ f }) => {
  const { fps } = useVideoConfig();
  const g = spring({ frame: f - S.zoom[0], fps, config: { damping: 200 } });
  const scale = interpolate(g, [0, 1], [0.9, 1]);
  const fade = interpolate(g, [0, 1], [0, 1]);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{
        transform: `scale(${scale})`, opacity: fade,
        background: T.panel, border: `1px solid #2E2E38`, borderRadius: 4,
        padding: "34px 46px", boxShadow: "0 30px 90px rgba(0,0,0,.55)",
      }}>
        <Line text="zone 1   keeps 0.50   a clear break, 191x the noise" color={T.zone} />
        <div style={{ height: 14 }} />
        <Line text="stop here     below~56" color={T.accent} />
        <Line text='              "ok good we got the plan settled"' dim />
      </div>
    </AbsoluteFill>
  );
};

/** Scene 6: the Rewind picker, scrolling until the counter reads 56. */
const Picker: React.FC<{ f: number }> = ({ f }) => {
  const p = at(f, S.picker);
  const counter = Math.round(interpolate(p, [0.05, 0.8], [4, 56], { extrapolateRight: "clamp" }));
  const menuOpen = f >= S.menu[0];
  const pick = menuOpen
    ? Math.min(4, Math.floor(interpolate(at(f, S.menu), [0.05, 0.32], [0, 4],
        { extrapolateRight: "clamp" })))
    : -1;
  const noteChars = menuOpen
    ? Math.floor(interpolate(at(f, S.menu), [0.42, 0.95], [0, NOTE.length],
        { extrapolateRight: "clamp" }))
    : 0;

  return (
    <AbsoluteFill style={{ background: "rgba(10,10,13,.72)" }}>
      <div style={{
        position: "absolute", left: T.padX, right: T.padX, top: 120,
        background: T.bg, border: `1px solid #2E2E38`, padding: "26px 30px",
      }}>
        <Line text="Rewind" color={T.accent} />
        <div style={{ height: 8 }} />
        <Line text="Restore the code and/or conversation to the point before…" dim />
        <div style={{ height: 16 }} />
        <Line text={`  ↑ ${132 - counter} more above`} dim />
        <div style={{ height: 10 }} />
        {PICKER.map((t, i) => (
          <div key={i} style={{ marginBottom: 10 }}>
            <Line text={(i === 2 ? "› " : "  ") + t}
                  color={i === 2 ? T.ink : T.dim} />
            {t !== "(current)" && <Line text="   No code changes" color={T.faint} />}
          </div>
        ))}
        <div style={{ height: 6 }} />
        <Line text={`  ↓ ${counter} more below`}
              color={counter >= 56 ? T.accent : T.dim} />

        {menuOpen && (
          <div style={{ marginTop: 22, borderTop: `1px solid #2E2E38`, paddingTop: 18 }}>
            {MENU.map((m, i) => (
              <Line key={i} text={(i === pick ? "❯ " : "  ") + m}
                    color={i === pick ? T.accent : T.dim} />
            ))}
            {noteChars > 0 && (
              <div style={{ marginTop: 14 }}>
                <Line text={"  add context: " + NOTE.slice(0, noteChars)} color={T.ink} />
              </div>
            )}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

/** Scene 8: the summary replaces the past. */
const Summarize: React.FC<{ f: number }> = ({ f }) => {
  const p = at(f, S.summarize);
  const collapse = interpolate(p, [0.15, 0.7], [1, 0], { extrapolateRight: "clamp" });
  const done = p > 0.72;
  return (
    <div style={{ position: "absolute", top: 70, left: T.padX, right: T.padX }}>
      <div style={{ opacity: collapse, transform: `scaleY(${Math.max(collapse, 0.02)})`,
                    transformOrigin: "top" }}>
        {HISTORY.map(([who, text], i) => (
          <div key={i} style={{ marginBottom: 6, opacity: 0.5 }}>
            <Line text={(who === "user" ? "› " : "● ") + text} dim />
          </div>
        ))}
      </div>
      <div style={{ marginTop: 8 }}>
        <Line text={done ? "● Summary of the earlier work"
                         : "  ✻ Summarizing up to that message…"}
              color={done ? T.good : T.dim} />
        {done && (
          <>
            <Line text="  The retry path and its backoff are done and reviewed." dim />
            <Line text="  Nothing is committed. The cache layer is next." dim />
          </>
        )}
      </div>
    </div>
  );
};

/** Scene 9: back to work, with room to breathe. */
const Back: React.FC<{ f: number }> = ({ f }) => {
  const p = at(f, S.back);
  const typed = "ok, now the cache layer".slice(
    0, Math.floor(interpolate(p, [0.35, 0.9], [0, 23], { extrapolateRight: "clamp" })));
  return (
    <div style={{ position: "absolute", top: 70, left: T.padX, right: T.padX }}>
      <Line text="● Summary of the earlier work" color={T.good} />
      <Line text="  The retry path and its backoff are done and reviewed." dim />
      <Line text="  Nothing is committed. The cache layer is next." dim />
      <div style={{ height: 22 }} />
      <Line text={"› " + typed} />
    </div>
  );
};

/** Scene 10: the end card. */
const Card: React.FC<{ f: number }> = ({ f }) => {
  const { fps } = useVideoConfig();
  const g = spring({ frame: f - S.card[0], fps, config: { damping: 200 } });
  return (
    <AbsoluteFill style={{
      background: T.bg, justifyContent: "center", alignItems: "center",
      opacity: interpolate(f, [S.card[0], S.card[0] + 10], [0, 1], { extrapolateRight: "clamp" }),
    }}>
      <div style={{ transform: `translateY(${interpolate(g, [0, 1], [16, 0])}px)`,
                    textAlign: "center" }}>
        <Mark size={128} />
        <div style={{ fontFamily: T.mono, fontSize: 46, color: T.ink,
                      marginTop: 18, letterSpacing: -1 }}>context-keep</div>
        <div style={{ fontFamily: T.mono, fontSize: 21, color: T.dim, marginTop: 14 }}>
          Find where a long chat can be summarized.
        </div>
        <div style={{ marginTop: 42, background: T.panel, border: "1px solid #2E2E38",
                      borderRadius: 4, padding: "22px 30px", textAlign: "left" }}>
          <div style={{ fontFamily: T.mono, fontSize: 20, color: T.accent }}>
            /plugin marketplace add unclecode/context-keep
          </div>
          <div style={{ fontFamily: T.mono, fontSize: 20, color: T.accent, marginTop: 8 }}>
            /plugin install context-keep@context-keep
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Demo: React.FC = () => {
  const f = useCurrentFrame();
  const pct = f < S.summarize[0] ? 81
    : f < S.back[0] ? interpolate(f, [S.summarize[0] + 30, S.back[0]], [81, 29],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : 29;

  return (
    <AbsoluteFill style={{ background: T.bg }}>
      <Shell>
        {f < S.summarize[0] && <Session f={f} />}
        {within(f, S.zoom) && <Zoom f={f} />}
        {(within(f, S.picker) || within(f, S.menu)) && <Picker f={f} />}
        {within(f, S.summarize) && <Summarize f={f} />}
        {within(f, S.back) && <Back f={f} />}
        {f < S.card[0] && <StatusBar pct={pct} />}
      </Shell>
      {f >= S.card[0] && <Card f={f} />}
    </AbsoluteFill>
  );
};
