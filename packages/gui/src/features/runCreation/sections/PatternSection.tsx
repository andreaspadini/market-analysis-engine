import React, { useCallback } from "react";
import { Card, CardHeader, CardTitle } from "../../../components/ui/Card";
import { Stack } from "../../../components/layout/Stack";
import { Grid } from "../../../components/layout/Grid";
import {
  ManualPatternCandle,
  ManualPatternClosePosition,
  ManualPatternDirection,
  useRunCreationState,
} from "../state/useRunCreationState";

type EngineKey = "pattern";

function FieldRow(props: { label: string; children: React.ReactNode }) {
  return (
    <Stack gap={6}>
      <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>{props.label}</label>
      {props.children}
    </Stack>
  );
}

function NumberInput(props: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  step?: number;
}) {
  return (
    <input
      type="number"
      value={Number.isFinite(props.value) ? String(props.value) : "0"}
      min={props.min}
      step={props.step ?? "any"}
      onChange={(e) => props.onChange(Number(e.target.value))}
      style={{ width: "100%", padding: 8, borderRadius: 8 }}
    />
  );
}

function SelectInput<T extends string>(props: {
  value: T;
  options: T[];
  onChange: (v: T) => void;
}) {
  return (
    <select
      value={props.value}
      onChange={(e) => props.onChange(e.target.value as T)}
      style={{ width: "100%", padding: 8, borderRadius: 8 }}
    >
      {props.options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
}

export function PatternSection() {
  const { pipelineParametersV1, setEngineField } = useRunCreationState();
  const p = pipelineParametersV1.engines.pattern;

  const setAny = useCallback(
    (path: string, v: unknown) => setEngineField("pattern" as EngineKey, path, v),
    [setEngineField]
  );

  const updateCandles = useCallback(
    (next: ManualPatternCandle[]) => {
      const normalized = next.map((candle, idx) => ({ ...candle, index: idx + 1 }));
      setAny("candles", normalized);
      setAny("length_bars", normalized.length);
    },
    [setAny]
  );

  const updateCandle = useCallback(
    (index: number, patch: Partial<ManualPatternCandle>) => {
      updateCandles(p.candles.map((candle, idx) => (idx === index ? { ...candle, ...patch } : candle)));
    },
    [p.candles, updateCandles]
  );

  const addCandle = useCallback(() => {
    const last = p.candles[p.candles.length - 1];
    const next: ManualPatternCandle = last
      ? { ...last, index: p.candles.length + 1 }
      : {
          index: 1,
          direction: "bullish",
          body_ticks: 0,
          upper_wick_ticks: 0,
          lower_wick_ticks: 0,
          volume: null,
          delta: null,
          close_position: "any",
        };

    updateCandles([...p.candles, next]);
  }, [p.candles, updateCandles]);

  const duplicateCandle = useCallback(
    (index: number) => {
      const source = p.candles[index];
      if (!source) return;
      const next = [...p.candles.slice(0, index + 1), { ...source }, ...p.candles.slice(index + 1)];
      updateCandles(next);
    },
    [p.candles, updateCandles]
  );

  const deleteCandle = useCallback(
    (index: number) => {
      if (p.candles.length <= 1) return;
      updateCandles(p.candles.filter((_, idx) => idx !== index));
    },
    [p.candles, updateCandles]
  );

  const payloadPreview = {
    mode: p.mode,
    tick_size: p.tick_size,
    length_bars: p.candles.length,
    tolerance: p.tolerance,
    candles: p.candles,
    visualization: p.visualization,
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Manual Pattern Builder</CardTitle>
      </CardHeader>

      <div style={{ padding: 16 }}>
        <Stack gap={18}>
          <Grid columns="1fr 1fr 1fr" gap={16}>
            <FieldRow label="tick_size">
              <NumberInput
                value={p.tick_size}
                min={0.000001}
                step={0.01}
                onChange={(v) => setAny("tick_size", v)}
              />
            </FieldRow>

            <FieldRow label="pattern length">
              <NumberInput value={p.candles.length} min={1} onChange={() => undefined} />
            </FieldRow>

            <FieldRow label="mode">
              <input
                value={p.mode}
                readOnly
                style={{
                  width: "100%",
                  padding: 8,
                  borderRadius: 8,
                  opacity: 0.75,
                }}
              />
            </FieldRow>
          </Grid>

          <div style={{ border: "1px solid var(--border)", borderRadius: 12, overflowX: "auto" }}>
            <div style={{ padding: 12, fontWeight: 700 }}>Candles</div>

            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 980 }}>
              <thead>
                <tr>
                  {[
                    "Candle",
                    "Dir",
                    "Body",
                    "Upper Wick",
                    "Lower Wick",
                    "Volume",
                    "Delta",
                    "Close Pos",
                    "Actions",
                  ].map((header) => (
                    <th
                      key={header}
                      style={{
                        textAlign: "left",
                        fontSize: 12,
                        padding: 8,
                        borderTop: "1px solid var(--border)",
                        borderBottom: "1px solid var(--border)",
                        opacity: 0.75,
                      }}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {p.candles.map((candle, idx) => (
                  <tr key={`${candle.index}-${idx}`}>
                    <td style={{ padding: 8, borderBottom: "1px solid var(--border)" }}>{idx + 1}</td>

                    <td style={{ padding: 8, borderBottom: "1px solid var(--border)" }}>
                      <SelectInput<ManualPatternDirection>
                        value={candle.direction}
                        options={["bullish", "bearish", "neutral", "any"]}
                        onChange={(v) => updateCandle(idx, { direction: v })}
                      />
                    </td>

                    <td style={{ padding: 8, borderBottom: "1px solid var(--border)" }}>
                      <NumberInput
                        value={candle.body_ticks}
                        min={0}
                        onChange={(v) => updateCandle(idx, { body_ticks: v })}
                      />
                    </td>

                    <td style={{ padding: 8, borderBottom: "1px solid var(--border)" }}>
                      <NumberInput
                        value={candle.upper_wick_ticks}
                        min={0}
                        onChange={(v) => updateCandle(idx, { upper_wick_ticks: v })}
                      />
                    </td>

                    <td style={{ padding: 8, borderBottom: "1px solid var(--border)" }}>
                      <NumberInput
                        value={candle.lower_wick_ticks}
                        min={0}
                        onChange={(v) => updateCandle(idx, { lower_wick_ticks: v })}
                      />
                    </td>

                    <td style={{ padding: 8, borderBottom: "1px solid var(--border)" }}>
                      <NumberInput
                        value={candle.volume ?? 0}
                        min={0}
                        onChange={(v) => updateCandle(idx, { volume: Number.isFinite(v) ? v : null })}
                      />
                    </td>

                    <td style={{ padding: 8, borderBottom: "1px solid var(--border)" }}>
                      <NumberInput
                        value={candle.delta ?? 0}
                        onChange={(v) => updateCandle(idx, { delta: Number.isFinite(v) ? v : null })}
                      />
                    </td>

                    <td style={{ padding: 8, borderBottom: "1px solid var(--border)" }}>
                      <SelectInput<ManualPatternClosePosition>
                        value={candle.close_position}
                        options={["near_high", "near_low", "mid", "any"]}
                        onChange={(v) => updateCandle(idx, { close_position: v })}
                      />
                    </td>

                    <td style={{ padding: 8, borderBottom: "1px solid var(--border)", whiteSpace: "nowrap" }}>
                      <button type="button" onClick={() => duplicateCandle(idx)} style={{ marginRight: 8 }}>
                        Duplicate
                      </button>
                      <button type="button" onClick={() => deleteCandle(idx)} disabled={p.candles.length <= 1}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ padding: 12 }}>
              <button type="button" onClick={addCandle}>
                + Add candle
              </button>
            </div>
          </div>

          <div style={{ border: "1px solid var(--border)", borderRadius: 12, padding: 12 }}>
            <Stack gap={12}>
              <div style={{ fontWeight: 700 }}>Tolerance Controls</div>

              <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                <FieldRow label="body_ticks_pct">
                  <NumberInput
                    value={p.tolerance.body_ticks_pct}
                    min={0.000001}
                    step={0.1}
                    onChange={(v) => setAny("tolerance.body_ticks_pct", v)}
                  />
                </FieldRow>

                <FieldRow label="wick_ticks_pct">
                  <NumberInput
                    value={p.tolerance.wick_ticks_pct}
                    min={0.000001}
                    step={0.1}
                    onChange={(v) => setAny("tolerance.wick_ticks_pct", v)}
                  />
                </FieldRow>

                <FieldRow label="volume_pct">
                  <NumberInput
                    value={p.tolerance.volume_pct}
                    min={0.000001}
                    step={0.1}
                    onChange={(v) => setAny("tolerance.volume_pct", v)}
                  />
                </FieldRow>

                <FieldRow label="delta_pct">
                  <NumberInput
                    value={p.tolerance.delta_pct}
                    min={0.000001}
                    step={0.1}
                    onChange={(v) => setAny("tolerance.delta_pct", v)}
                  />
                </FieldRow>
              </Grid>
            </Stack>
          </div>

          <div style={{ border: "1px solid var(--border)", borderRadius: 12, padding: 12 }}>
            <Stack gap={12}>
              <div style={{ fontWeight: 700 }}>Context Visualization</div>

              <Grid columns="1fr 1fr" gap={16}>
                <FieldRow label="context_before_bars">
                  <NumberInput
                    value={p.visualization.context_before_bars}
                    min={0}
                    step={1}
                    onChange={(v) => setAny("visualization.context_before_bars", Math.max(0, Math.floor(v)))}
                  />
                </FieldRow>

                <FieldRow label="context_after_bars">
                  <NumberInput
                    value={p.visualization.context_after_bars}
                    min={0}
                    step={1}
                    onChange={(v) => setAny("visualization.context_after_bars", Math.max(0, Math.floor(v)))}
                  />
                </FieldRow>
              </Grid>
            </Stack>
          </div>

          <div style={{ border: "1px solid var(--border)", borderRadius: 12, padding: 12 }}>
            <Stack gap={12}>
              <div style={{ fontWeight: 700 }}>Payload Preview</div>

              <pre
                style={{
                  margin: 0,
                  padding: 12,
                  borderRadius: 10,
                  overflowX: "auto",
                  background: "color-mix(in srgb, var(--panel) 88%, black)",
                  fontSize: 12,
                }}
              >
                {JSON.stringify(payloadPreview, null, 2)}
              </pre>
            </Stack>
          </div>
        </Stack>
      </div>
    </Card>
  );
}