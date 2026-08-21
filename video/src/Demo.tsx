import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { T, S, ZOOMS } from "./theme";
import { HISTORY, REPORT, PICKER, MENU, NOTE } from "./data";
import { Mark, Line, Foot, Shell, Scroll } from "./parts";

const within = (f: number, [a, b]: readonly [number, number]) => f >= a && f < b;
const at = (f: number, [a, b]: readonly [number, number]) => (f - a) / (b - a);

/** How far into a zoom move we are: 0 wide, 1 close. */
const zoomAmount = (f: number, z: typeof ZOOMS[number]) =>
  f < z.a || f > z.d ? 0
    : f < z.b ? interpolate(f, [z.a, z.b], [0, 1])
    : f <= z.c ? 1
    : interpolate(f, [z.c, z.d], [1, 0]);

/** Everything the terminal has printed so far, oldest first. */
const Transcript: React.FC<{ f: number }> = ({ f }) => {
  const shown = f < S.printing[0] ? 0
    : Math.min(REPORT.length, Math.floor(at(f, S.printing) * REPORT.length * 1.3));
  const chartCols = f < S.printing[0] ? 0
    : Math.floor(interpolate(f, [S.printing[0] + 22, S.printing[0] + 84], [0, 60],
        { extrapolateRight: "clamp" }));
  const isChart = (i: number) => i >= 3 && i <= 12;

  return (
    <>
      {HISTORY.map(([who, text], i) => (
        <Line key={i} text={(who === "user" ? "› " : "● ") + text}
              color={who === "user" ? T.ink : T.dim} />
      ))}
      {f >= S.running[0] && (
        <>
          <div style={{ height: T.lh / 2 }} />
          <Line text="› /keep" />
          <Line text={f < S.printing[0] ? "  ✳ Working…" : "  Ran 1 shell command"} dim />
        </>
      )}
      {f >= S.printing[0] && (
        <>
          <div style={{ height: T.lh / 2 }} />
          {REPORT.slice(0, shown).map((l, i) => (
            <Line key={i}
                  text={isChart(i) ? l.slice(0, Math.max(0, chartCols + 7)) : l}
                  color={l.includes("zone 1") ? T.zone
                       : l.includes("below~56") ? T.accent : undefined}
                  dim={l.trim().startsWith("keep ") || l.includes("older →")} />
          ))}
        </>
      )}
    </>
  );
};

/** The Rewind picker, drawn over the session. */
const Picker: React.FC<{ f: number }> = ({ f }) => {
  const p = at(f, S.picker);
  const counter = Math.round(
    interpolate(p, [0.06, 0.78], [4, 56], { extrapolateRight: "clamp" }));
  const menuOpen = f >= S.menu[0];
  const pick = menuOpen
    ? Math.min(4, Math.floor(interpolate(at(f, S.menu), [0.04, 0.30], [0, 4],
        { extrapolateRight: "clamp" })))
    : -1;
  const noteChars = menuOpen
    ? Math.floor(interpolate(at(f, S.menu), [0.40, 0.94], [0, NOTE.length],
        { extrapolateRight: "clamp" }))
    : 0;

  return (
    <AbsoluteFill style={{ background: "rgba(6,6,8,.80)" }}>
      <div style={{
        position: "absolute", left: T.padX, right: T.padX, top: 70,
        background: T.bg, border: `1px solid ${T.rule}`, padding: "24px 28px",
      }}>
        <Line text="Rewind" color={T.accent} />
        <div style={{ height: 10 }} />
        <Line text={`  ↑ ${132 - counter} more above`} dim />
        <div style={{ height: 10 }} />
        {PICKER.map((t, i) => (
          <Line key={i} text={(i === 2 ? "› " : "  ") + t}
                color={i === 2 ? T.ink : T.dim} />
        ))}
        <div style={{ height: 10 }} />
        <Line text={`  ↓ ${counter} more below`}
              color={counter >= 56 ? T.accent : T.dim} />

        {menuOpen && (
          <div style={{ marginTop: 18, borderTop: `1px solid ${T.rule}`, paddingTop: 16 }}>
            {MENU.map((m, i) => (
              <Line key={i} text={(i === pick ? "❯ " : "  ") + m}
                    color={i === pick ? T.accent : T.dim} />
            ))}
            {noteChars > 0 && (
              <div style={{ marginTop: 12 }}>
                <Line text={"  add context: " + NOTE.slice(0, noteChars)} color={T.ink} />
              </div>
            )}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};

/** The past folds away and one summary block takes its place. */
const Summarize: React.FC<{ f: number }> = ({ f }) => {
  const p = at(f, S.summarize);
  const fold = interpolate(p, [0.12, 0.62], [1, 0], { extrapolateRight: "clamp" });
  const done = p > 0.66;
  return (
    <>
      <div style={{
        opacity: fold, transform: `scaleY(${Math.max(fold, 0.01)})`,
        transformOrigin: "bottom",
      }}>
        {HISTORY.map(([who, text], i) => (
          <Line key={i} text={(who === "user" ? "› " : "● ") + text} dim />
        ))}
      </div>
      <Line text={done ? "● Summary of the earlier work"
                       : "  ✳ Summarizing up to that message…"}
            color={done ? T.good : T.dim} />
      {done && (
        <>
          <Line text="  The retry path and its backoff are done and reviewed." dim />
          <Line text="  Nothing is committed. The cache layer is next." dim />
        </>
      )}
    </>
  );
};

/** The end card. */
const Card: React.FC<{ f: number }> = ({ f }) => {
  const { fps } = useVideoConfig();
  const g = spring({ frame: f - S.card[0], fps, config: { damping: 200 } });
  return (
    <AbsoluteFill style={{
      background: T.bg, justifyContent: "center", alignItems: "center",
      opacity: interpolate(f, [S.card[0], S.card[0] + 12], [0, 1],
        { extrapolateRight: "clamp" }),
    }}>
      <div style={{
        transform: `translateY(${interpolate(g, [0, 1], [22, 0])}px)`,
        textAlign: "center",
      }}>
        <Mark size={150} />
        <div style={{ fontFamily: T.mono, fontSize: 62, color: T.ink,
                      marginTop: 20, letterSpacing: -1 }}>context-keep</div>
        <div style={{ fontFamily: T.mono, fontSize: 28, color: T.dim, marginTop: 16 }}>
          Find where a long chat can be summarized.
        </div>
        <div style={{ marginTop: 46, background: T.panel, border: `1px solid ${T.rule}`,
                      padding: "26px 36px", textAlign: "left" }}>
          <div style={{ fontFamily: T.mono, fontSize: 26, color: T.accent }}>
            /plugin marketplace add unclecode/context-keep
          </div>
          <div style={{ fontFamily: T.mono, fontSize: 26, color: T.accent, marginTop: 10 }}>
            /plugin install context-keep@context-keep
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Demo: React.FC = () => {
  const f = useCurrentFrame();

  // The token count falls only while the summary is being written.
  const pct = f < S.summarize[0] ? 81
    : f < S.back[0] ? interpolate(f, [S.summarize[0] + 36, S.back[0]], [81, 29],
        { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
    : 29;

  const typed = within(f, S.typing)
    ? "/keep".slice(0, Math.floor(at(f, S.typing) * 5.6))
    : f >= S.typing[1] && f < S.running[0] ? "/keep"
    : within(f, S.back)
      ? "ok, now the cache layer".slice(0, Math.floor(
          interpolate(at(f, S.back), [0.30, 0.88], [0, 23], { extrapolateRight: "clamp" })))
      : "";

  const hint = f < S.printing[0] ? undefined
    : f < S.summarize[0] ? "Worked for 18s"
    : f < S.back[0] ? undefined : "Worked for 41s";

  // One zoom at a time, so the moves never fight each other.
  const active = ZOOMS.map((z) => ({ z, amt: zoomAmount(f, z) }))
                      .reduce((best, cur) => (cur.amt > best.amt ? cur : best),
                              { z: ZOOMS[0], amt: 0 });
  const scale = 1 + (active.z.scale - 1) * active.amt;
  const ox = active.z.ox * 100, oy = active.z.oy * 100;
  // Scaling alone keeps the target where it already sat, often at an edge.
  // This pan carries it to the middle of the frame, easing with the zoom.
  const panX = (0.5 - active.z.ox) * 1920 * active.amt;
  const panY = (0.5 - active.z.oy) * 1080 * active.amt;

  const showPicker = within(f, S.picker) || within(f, S.menu);

  return (
    <AbsoluteFill style={{ background: T.bg, overflow: "hidden" }}>
      <AbsoluteFill style={{
        transform: `translate(${panX}px, ${panY}px) scale(${scale})`,
        transformOrigin: `${ox}% ${oy}%`,
      }}>
        {f < S.card[0] && (
          <Shell>
            <Scroll>
              {f < S.summarize[0] && <Transcript f={f} />}
              {within(f, S.summarize) && <Summarize f={f} />}
              {within(f, S.back) && (
                <>
                  <Line text="● Summary of the earlier work" color={T.good} />
                  <Line text="  The retry path and its backoff are done and reviewed." dim />
                  <Line text="  Nothing is committed. The cache layer is next." dim />
                </>
              )}
            </Scroll>
            <Foot pct={pct} typed={typed} caret={Math.floor(f / 15) % 2 === 0}
                  hint={hint} chip="fetcher" />
            {showPicker && <Picker f={f} />}
          </Shell>
        )}
      </AbsoluteFill>
      {f >= S.card[0] && <Card f={f} />}
    </AbsoluteFill>
  );
};
