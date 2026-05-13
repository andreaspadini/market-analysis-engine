import React, { useCallback, useMemo, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Stack } from "../../../components/layout/Stack";
import { Grid } from "../../../components/layout/Grid";
import { Collapsible } from "../../../components/ui/Collapsible";
import type { RunCreationState } from "../state/useRunCreationState";

type EngineKey = "statistical";

function SectionGroup(props: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const { title, subtitle, children, defaultOpen } = props;

  return (
    <details
      open={defaultOpen ?? false}
      style={{
        border: "1px solid var(--border)",
        borderRadius: 12,
        background: "var(--panel)",
      }}
    >
      <summary
        style={{
          cursor: "pointer",
          padding: 12,
          userSelect: "none",
          listStyle: "none",
          background: "color-mix(in srgb, var(--panel) 92%, black)",
          borderBottom: "1px solid var(--border)",
          borderTopLeftRadius: 12,
          borderTopRightRadius: 12,
        }}
      >
        <Stack gap={4}>
          <div style={{ fontWeight: 700 }}>{title}</div>
          {subtitle ? (
            <div style={{ fontSize: 12, opacity: 0.72 }}>{subtitle}</div>
          ) : null}
        </Stack>
      </summary>
      <div style={{ padding: 12 }}>{children}</div>
    </details>
  );
}

function FieldRow(props: { label: string; children: React.ReactNode }) {
  return (
    <Stack gap={6}>
      <label style={{ display: "block", fontSize: 12, opacity: 0.8 }}>
        {props.label}
      </label>
      {props.children}
    </Stack>
  );
}

function TextInput(props: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <input
      type="text"
      value={props.value}
      onChange={(e) => props.onChange(e.target.value)}
      placeholder={props.placeholder}
      style={{ width: "100%", padding: 8, borderRadius: 8 }}
    />
  );
}

function NumberInput(props: { value: number; onChange: (v: number) => void }) {
  return (
    <input
      type="number"
      value={Number.isFinite(props.value) ? String(props.value) : "0"}
      onChange={(e) => props.onChange(Number(e.target.value))}
      style={{ width: "100%", padding: 8, borderRadius: 8 }}
    />
  );
}

function BoolInput(props: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <input
        type="checkbox"
        checked={props.checked}
        onChange={(e) => props.onChange(e.target.checked)}
      />
      <span style={{ fontSize: 13, opacity: 0.9 }}>
        {props.checked ? "true" : "false"}
      </span>
    </label>
  );
}

function LinesEditor(props: {
  value: string[];
  placeholder?: string;
  onChange: (next: string[]) => void;
}) {
  const text = useMemo(() => (props.value ?? []).join("\n"), [props.value]);

  return (
    <textarea
      value={text}
      onChange={(e) => {
        const items = e.target.value
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean);
        props.onChange(items);
      }}
      rows={6}
      placeholder={props.placeholder}
      style={{ width: "100%", padding: 8, borderRadius: 8, resize: "vertical" }}
    />
  );
}

function JsonEditor(props: {
  label: string;
  value: unknown;
  onApply: (next: unknown) => void;
  rows?: number;
}) {
  const [draft, setDraft] = useState<string>(() =>
    JSON.stringify(props.value ?? {}, null, 2)
  );

  React.useEffect(() => {
    setDraft(JSON.stringify(props.value ?? {}, null, 2));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(props.value ?? {})]);

  return (
    <Stack gap={8}>
      <div style={{ fontSize: 12, opacity: 0.8 }}>{props.label}</div>
      <textarea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        rows={props.rows ?? 10}
        style={{
          width: "100%",
          padding: 8,
          borderRadius: 8,
          resize: "vertical",
          fontFamily: "monospace",
        }}
      />
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button
          type="button"
          onClick={() => {
            try {
              const parsed = JSON.parse(draft);
              props.onApply(parsed);
            } catch {
              // keep strict-safe behavior: no apply on invalid JSON
            }
          }}
          style={{
            padding: "8px 12px",
            borderRadius: 10,
            border: "1px solid var(--border)",
            background: "var(--panel)",
            cursor: "pointer",
          }}
        >
          Apply JSON
        </button>
      </div>
    </Stack>
  );
}

export function StatisticalSection({
  runCreation,
}: {
  runCreation: RunCreationState;
}) {
  const { pipelineParametersV1, setEngineField } = runCreation;
  const s = pipelineParametersV1.engines.statistical;

  const setText = useCallback(
    (path: string, v: string) =>
      setEngineField("statistical" as EngineKey, path, v),
    [setEngineField]
  );

  const setNum = useCallback(
    (path: string, v: number) =>
      setEngineField("statistical" as EngineKey, path, v),
    [setEngineField]
  );

  const setBool = useCallback(
    (path: string, v: boolean) =>
      setEngineField("statistical" as EngineKey, path, v),
    [setEngineField]
  );

  const setAny = useCallback(
    (path: string, v: unknown) =>
      setEngineField("statistical" as EngineKey, path, v),
    [setEngineField]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Statistical Engine</CardTitle>
      </CardHeader>

      <CardContent>
        <Stack gap={16}>
          <div className="subtle">
            Core statistical settings are shown first. Mapping, definitions and
            JSON editors are available in advanced sections.
          </div>

          <Collapsible
            title="Core settings"
            subtitle="Common statistical engine configuration"
            defaultOpen={true}
          >
            <Stack gap={16}>
              <SectionGroup
                title="Configuration"
                subtitle="statistical.config"
                defaultOpen={true}
              >
                <Stack gap={16}>
                  <Grid columns="1fr" gap={16}>
                    <FieldRow label="Version">
                      <TextInput
                        value={(s.config.version as string) ?? ""}
                        onChange={(v) => setText("config.version", v)}
                      />
                    </FieldRow>
                  </Grid>

                  <SectionGroup
                    title="Targets"
                    subtitle="statistical.config.targets"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr" gap={16}>
                      <Stack gap={12}>
                        <div style={{ fontWeight: 700, opacity: 0.9 }}>
                          Primary target
                        </div>
                        <FieldRow label="Primary target name">
                          <TextInput
                            value={(s.config.targets.primary.name as string) ?? ""}
                            onChange={(v) =>
                              setText("config.targets.primary.name", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="Primary ATR multiplier">
                          <NumberInput
                            value={Number(
                              s.config.targets.primary.atr_multiplier
                            )}
                            onChange={(v) =>
                              setNum("config.targets.primary.atr_multiplier", v)
                            }
                          />
                        </FieldRow>
                      </Stack>

                      <Stack gap={12}>
                        <div style={{ fontWeight: 700, opacity: 0.9 }}>
                          Secondary target
                        </div>
                        <FieldRow label="Secondary target name">
                          <TextInput
                            value={(s.config.targets.secondary.name as string) ?? ""}
                            onChange={(v) =>
                              setText("config.targets.secondary.name", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="Secondary ticks">
                          <NumberInput
                            value={Number(s.config.targets.secondary.ticks)}
                            onChange={(v) =>
                              setNum("config.targets.secondary.ticks", v)
                            }
                          />
                        </FieldRow>
                      </Stack>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Target scans"
                    subtitle="Base target ATR"
                    defaultOpen={false}
                  >
                    <Stack gap={16}>
                      <FieldRow label="config.target_scans.success_ATR_scan.base_target">
                        <TextInput
                          value={
                            (s.config.target_scans.success_ATR_scan
                              .base_target as string) ?? ""
                          }
                          onChange={(v) =>
                            setText(
                              "config.target_scans.success_ATR_scan.base_target",
                              v
                            )
                          }
                        />
                      </FieldRow>

                      <SectionGroup
                        title="ATR X scan"
                        subtitle="statistical.config.target_scans.success_ATR_scan.x_scan"
                        defaultOpen={false}
                      >
                        <Grid columns="1fr 1fr 1fr" gap={16}>
                          <FieldRow label="Scan start">
                            <NumberInput
                              value={Number(
                                s.config.target_scans.success_ATR_scan.x_scan
                                  .start
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.target_scans.success_ATR_scan.x_scan.start",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="Scan end">
                            <NumberInput
                              value={Number(
                                s.config.target_scans.success_ATR_scan.x_scan.end
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.target_scans.success_ATR_scan.x_scan.end",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="Scan step">
                            <NumberInput
                              value={Number(
                                s.config.target_scans.success_ATR_scan.x_scan.step
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.target_scans.success_ATR_scan.x_scan.step",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                        </Grid>
                      </SectionGroup>
                    </Stack>
                  </SectionGroup>

                  <SectionGroup
                    title="Tick scan"
                    subtitle="statistical.config.tick_scan"
                    defaultOpen={false}
                  >
                    <Stack gap={16}>
                      <FieldRow label="Tick size">
                        <NumberInput
                          value={Number(s.config.tick_scan.tick_size)}
                          onChange={(v) => setNum("config.tick_scan.tick_size", v)}
                        />
                      </FieldRow>

                      <Grid columns="1fr 1fr" gap={16}>
                        <FieldRow label="Success tick levels">
                          <LinesEditor
                            value={(s.config.tick_scan.success_ticks.levels ?? [])
                              .map(String)
                              .map((x) => x)}
                            onChange={(arr) =>
                              setAny(
                                "config.tick_scan.success_ticks.levels",
                                arr.map((x) => Number(x))
                              )
                            }
                          />
                        </FieldRow>

                        <FieldRow label="Clean tick levels">
                          <LinesEditor
                            value={(s.config.tick_scan.clean_ticks.levels ?? [])
                              .map(String)
                              .map((x) => x)}
                            onChange={(arr) =>
                              setAny(
                                "config.tick_scan.clean_ticks.levels",
                                arr.map((x) => Number(x))
                              )
                            }
                          />
                        </FieldRow>
                      </Grid>
                    </Stack>
                  </SectionGroup>

                  <SectionGroup
                    title="Clean quant"
                    subtitle="statistical.config.clean_quant"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr" gap={16}>
                      <FieldRow label="Base target">
                        <TextInput
                          value={(s.config.clean_quant.base_target as string) ?? ""}
                          onChange={(v) =>
                            setText("config.clean_quant.base_target", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="ATR multiplier">
                        <NumberInput
                          value={Number(s.config.clean_quant.atr_multiplier)}
                          onChange={(v) =>
                            setNum("config.clean_quant.atr_multiplier", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="Clean ATR threshold">
                        <NumberInput
                          value={Number(
                            s.config.clean_quant.clean_atr_threshold
                          )}
                          onChange={(v) =>
                            setNum("config.clean_quant.clean_atr_threshold", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Buckets"
                    subtitle="statistical.config.bucketizers"
                    defaultOpen={false}
                  >
                    <Stack gap={16}>
                      <SectionGroup
                        title="Volume bucket"
                        subtitle="statistical.config.bucketizers.volume_bucket"
                        defaultOpen={false}
                      >
                        <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                          <FieldRow label="Very low max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.volume_bucket?.very_low_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.volume_bucket.very_low_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="Low max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.volume_bucket?.low_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.volume_bucket.low_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="Medium max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.volume_bucket?.medium_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.volume_bucket.medium_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="High max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.volume_bucket?.high_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.volume_bucket.high_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                        </Grid>
                      </SectionGroup>

                      <SectionGroup
                        title="Delta bucket"
                        subtitle="statistical.config.bucketizers.delta_bucket"
                        defaultOpen={false}
                      >
                        <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                          <FieldRow label="0-100 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.delta_bucket?.delta_0_100_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.delta_bucket.delta_0_100_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="100-300 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.delta_bucket?.delta_100_300_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.delta_bucket.delta_100_300_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="300-600 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.delta_bucket?.delta_300_600_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.delta_bucket.delta_300_600_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="600-1000 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.delta_bucket?.delta_600_1000_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.delta_bucket.delta_600_1000_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                        </Grid>
                      </SectionGroup>

                      <SectionGroup
                        title="Compression bucket"
                        subtitle="statistical.config.bucketizers.compression_bucket"
                        defaultOpen={false}
                      >
                        <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                          <FieldRow label="Ultra compressed max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.compression_bucket?.ultra_compressed_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.compression_bucket.ultra_compressed_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="Compressed max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.compression_bucket?.compressed_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.compression_bucket.compressed_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="Balanced max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.compression_bucket?.balanced_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.compression_bucket.balanced_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="Expanded max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.compression_bucket?.expanded_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.compression_bucket.expanded_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                        </Grid>
                      </SectionGroup>

                      <SectionGroup
                        title="ATR bucket"
                        subtitle="statistical.config.bucketizers.atr_bucket"
                        defaultOpen={false}
                      >
                        <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                          <FieldRow label="0.0-0.5 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.atr_bucket?.atr_0_0_5_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.atr_bucket.atr_0_0_5_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="0.5-1.0 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.atr_bucket?.atr_0_5_1_0_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.atr_bucket.atr_0_5_1_0_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="1.0-1.5 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.atr_bucket?.atr_1_0_1_5_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.atr_bucket.atr_1_0_1_5_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="1.5-2.5 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.atr_bucket?.atr_1_5_2_5_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.atr_bucket.atr_1_5_2_5_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                        </Grid>
                      </SectionGroup>

                      <SectionGroup
                        title="Pre breakout bucket"
                        subtitle="statistical.config.bucketizers.pre_bo_bucket"
                        defaultOpen={false}
                      >
                        <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                          <FieldRow label="Negative max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.pre_bo_bucket?.pre_neg_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.pre_bo_bucket.pre_neg_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="0-2 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.pre_bo_bucket?.pre_0_2_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.pre_bo_bucket.pre_0_2_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="2-4 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.pre_bo_bucket?.pre_2_4_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.pre_bo_bucket.pre_2_4_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="4-6 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.pre_bo_bucket?.pre_4_6_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.pre_bo_bucket.pre_4_6_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                        </Grid>
                      </SectionGroup>

                      <SectionGroup
                        title="Time bucket"
                        subtitle="statistical.config.bucketizers.time_bucket"
                        defaultOpen={false}
                      >
                        <Grid columns="1fr 1fr 1fr" gap={16}>
                          <FieldRow label="00-04 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.time_bucket?.tb_00_04_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.time_bucket.tb_00_04_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="04-08 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.time_bucket?.tb_04_08_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.time_bucket.tb_04_08_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="08-12 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.time_bucket?.tb_08_12_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.time_bucket.tb_08_12_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="12-16 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.time_bucket?.tb_12_16_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.time_bucket.tb_12_16_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="16-20 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.time_bucket?.tb_16_20_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.time_bucket.tb_16_20_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="20-24 max">
                            <NumberInput
                              value={Number(
                                s.config.bucketizers?.time_bucket?.tb_20_24_max ?? 0
                              )}
                              onChange={(v) =>
                                setNum(
                                  "config.bucketizers.time_bucket.tb_20_24_max",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                        </Grid>
                      </SectionGroup>
                    </Stack>
                  </SectionGroup>
                 
                  <SectionGroup
                    title="Machine learning"
                    subtitle="statistical.config.ml"
                    defaultOpen={false}
                  >
                    <Stack gap={16}>
                      <Grid columns="1fr 1fr" gap={16}>
                        <FieldRow label="Numeric features">
                          <LinesEditor
                            value={s.config.ml.numeric_features ?? []}
                            onChange={(arr) =>
                              setAny("config.ml.numeric_features", arr)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="Categorical features">
                          <LinesEditor
                            value={s.config.ml.categorical_features ?? []}
                            onChange={(arr) =>
                              setAny("config.ml.categorical_features", arr)
                            }
                          />
                        </FieldRow>
                      </Grid>

                      <Grid columns="1fr 1fr" gap={16}>
                        <FieldRow label="Target">
                          <TextInput
                            value={(s.config.ml.target as string) ?? ""}
                            onChange={(v) => setText("config.ml.target", v)}
                          />
                        </FieldRow>
                        <FieldRow label="Train ratio">
                          <NumberInput
                            value={Number(s.config.ml.train_ratio)}
                            onChange={(v) =>
                              setNum("config.ml.train_ratio", v)
                            }
                          />
                        </FieldRow>
                      </Grid>
                    </Stack>
                  </SectionGroup>

                  <SectionGroup
                    title="Statistics"
                    subtitle="statistical.config.statistics"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr" gap={16}>
                      <FieldRow label="Enabled blocks">
                        <LinesEditor
                          value={s.config.statistics.enabled_blocks ?? []}
                          onChange={(arr) =>
                            setAny("config.statistics.enabled_blocks", arr)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="Minimum sample size">
                        <NumberInput
                          value={Number(s.config.statistics.min_sample_size)}
                          onChange={(v) =>
                            setNum("config.statistics.min_sample_size", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>
                </Stack>
              </SectionGroup>
            </Stack>
          </Collapsible>

          <Collapsible
            title="Advanced settings"
            subtitle="Mapping, definitions and advanced JSON configuration"
            defaultOpen={false}
          >
            <Stack gap={16}>
              <SectionGroup
                title="Advanced JSON"
                subtitle="statistical.config advanced JSON editors"
                defaultOpen={false}
              >
                <Stack gap={16}>
                  <SectionGroup
                    title="Buckets JSON"
                    subtitle="statistical.config.buckets"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="config.buckets"
                      value={s.config.buckets}
                      onApply={(next) => setAny("config.buckets", next)}
                      rows={14}
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Bucketizers JSON"
                    subtitle="statistical.config.bucketizers"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="config.bucketizers"
                      value={s.config.bucketizers}
                      onApply={(next) => setAny("config.bucketizers", next)}
                      rows={16}
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Sessions JSON"
                    subtitle='statistical.config.sessions'
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label='config.sessions (Record<string, ["HH:MM","HH:MM"]>)'
                      value={s.config.sessions}
                      onApply={(next) => setAny("config.sessions", next)}
                      rows={12}
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Time buckets JSON"
                    subtitle="statistical.config.time_buckets"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label='config.time_buckets (Record<string, ["HH:MM","HH:MM"]>)'
                      value={s.config.time_buckets}
                      onApply={(next) => setAny("config.time_buckets", next)}
                      rows={12}
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Edge score JSON"
                    subtitle="statistical.config.edge_score"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="config.edge_score"
                      value={s.config.edge_score}
                      onApply={(next) => setAny("config.edge_score", next)}
                      rows={10}
                    />
                  </SectionGroup>
                </Stack>
              </SectionGroup>

              <SectionGroup
                title="Mapping"
                subtitle="statistical.mapping"
                defaultOpen={false}
              >
                <Stack gap={16}>
                  <FieldRow label="mapping.version">
                    <TextInput
                      value={(s.mapping.version as string) ?? ""}
                      onChange={(v) => setText("mapping.version", v)}
                    />
                  </FieldRow>

                  <SectionGroup
                    title="Core fields JSON"
                    subtitle="statistical.mapping.core_fields"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.core_fields"
                      value={s.mapping.core_fields}
                      onApply={(next) => setAny("mapping.core_fields", next)}
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Directional JSON"
                    subtitle="statistical.mapping.directional"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.directional"
                      value={s.mapping.directional}
                      onApply={(next) => setAny("mapping.directional", next)}
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Prices JSON"
                    subtitle="statistical.mapping.prices"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.prices"
                      value={s.mapping.prices}
                      onApply={(next) => setAny("mapping.prices", next)}
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Balance structure JSON"
                    subtitle="statistical.mapping.balance_structure"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.balance_structure"
                      value={s.mapping.balance_structure}
                      onApply={(next) =>
                        setAny("mapping.balance_structure", next)
                      }
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Volume / delta / volatility JSON"
                    subtitle="statistical.mapping.volume_delta_volatility"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.volume_delta_volatility"
                      value={s.mapping.volume_delta_volatility}
                      onApply={(next) =>
                        setAny("mapping.volume_delta_volatility", next)
                      }
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Strength / follow JSON"
                    subtitle="statistical.mapping.strength_follow"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.strength_follow"
                      value={s.mapping.strength_follow}
                      onApply={(next) =>
                        setAny("mapping.strength_follow", next)
                      }
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Rotations JSON"
                    subtitle="statistical.mapping.rotations"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.rotations"
                      value={s.mapping.rotations}
                      onApply={(next) => setAny("mapping.rotations", next)}
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Pre-breakout JSON"
                    subtitle="statistical.mapping.pre_breakout"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.pre_breakout"
                      value={s.mapping.pre_breakout}
                      onApply={(next) =>
                        setAny("mapping.pre_breakout", next)
                      }
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Ranking JSON"
                    subtitle="statistical.mapping.ranking"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.ranking"
                      value={s.mapping.ranking}
                      onApply={(next) => setAny("mapping.ranking", next)}
                    />
                  </SectionGroup>

                  <SectionGroup
                    title="Meta JSON"
                    subtitle="statistical.mapping.meta"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="mapping.meta"
                      value={s.mapping.meta}
                      onApply={(next) => setAny("mapping.meta", next)}
                    />
                  </SectionGroup>
                </Stack>
              </SectionGroup>

              <SectionGroup
                title="Session definitions"
                subtitle="statistical.sessions_def"
                defaultOpen={false}
              >
                <Stack gap={16}>
                  <Grid columns="1fr 1fr" gap={16}>
                    <FieldRow label="sessions_def.version">
                      <TextInput
                        value={(s.sessions_def.version as string) ?? ""}
                        onChange={(v) => setText("sessions_def.version", v)}
                      />
                    </FieldRow>
                    <FieldRow label="sessions_def.timezone">
                      <TextInput
                        value={(s.sessions_def.timezone as string) ?? ""}
                        onChange={(v) => setText("sessions_def.timezone", v)}
                      />
                    </FieldRow>
                  </Grid>

                  <FieldRow label="sessions_def.fallback_session">
                    <TextInput
                      value={(s.sessions_def.fallback_session as string) ?? ""}
                      onChange={(v) =>
                        setText("sessions_def.fallback_session", v)
                      }
                    />
                  </FieldRow>

                  <SectionGroup
                    title="Sessions JSON"
                    subtitle="statistical.sessions_def.sessions"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label='sessions_def.sessions (Record<string, {start,end}>)'
                      value={s.sessions_def.sessions}
                      onApply={(next) => setAny("sessions_def.sessions", next)}
                      rows={12}
                    />
                  </SectionGroup>
                </Stack>
              </SectionGroup>

              <SectionGroup
                title="Target definitions"
                subtitle="statistical.targets_def"
                defaultOpen={false}
              >
                <Stack gap={16}>
                  <FieldRow label="targets_def.version">
                    <TextInput
                      value={(s.targets_def.version as string) ?? ""}
                      onChange={(v) => setText("targets_def.version", v)}
                    />
                  </FieldRow>

                  <SectionGroup
                    title="Base metrics"
                    subtitle="statistical.targets_def.base_metrics"
                    defaultOpen={false}
                  >
                    <Stack gap={16}>
                      <SectionGroup
                        title="Max excursion source"
                        subtitle="statistical.targets_def.base_metrics.max_excursion_source"
                        defaultOpen={false}
                      >
                        <Grid columns="1fr 1fr" gap={16}>
                          <FieldRow label="max_excursion_source.field">
                            <TextInput
                              value={
                                (s.targets_def.base_metrics.max_excursion_source
                                  .field as string) ?? ""
                              }
                              onChange={(v) =>
                                setText(
                                  "targets_def.base_metrics.max_excursion_source.field",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                          <FieldRow label="max_excursion_source.key">
                            <TextInput
                              value={
                                (s.targets_def.base_metrics.max_excursion_source
                                  .key as string) ?? ""
                              }
                              onChange={(v) =>
                                setText(
                                  "targets_def.base_metrics.max_excursion_source.key",
                                  v
                                )
                              }
                            />
                          </FieldRow>
                        </Grid>
                      </SectionGroup>

                      <SectionGroup
                        title="ATR source"
                        subtitle="statistical.targets_def.base_metrics.atr_source"
                        defaultOpen={false}
                      >
                        <FieldRow label="atr_source.field">
                          <TextInput
                            value={
                              (s.targets_def.base_metrics.atr_source
                                .field as string) ?? ""
                            }
                            onChange={(v) =>
                              setText(
                                "targets_def.base_metrics.atr_source.field",
                                v
                              )
                            }
                          />
                        </FieldRow>
                      </SectionGroup>
                    </Stack>
                  </SectionGroup>

                  <SectionGroup
                    title="Failure definition"
                    subtitle="statistical.targets_def.failure_definition"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr" gap={16}>
                      <FieldRow label="targets_def.failure_definition.field">
                        <TextInput
                          value={
                            (s.targets_def.failure_definition.field as string) ??
                            ""
                          }
                          onChange={(v) =>
                            setText("targets_def.failure_definition.field", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="targets_def.failure_definition.true_value">
                        <TextInput
                          value={
                            (s.targets_def.failure_definition
                              .true_value as string) ?? ""
                          }
                          onChange={(v) =>
                            setText(
                              "targets_def.failure_definition.true_value",
                              v
                            )
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Targets JSON"
                    subtitle="statistical.targets_def.targets"
                    defaultOpen={false}
                  >
                    <JsonEditor
                      label="targets_def.targets (Record<string, TargetDef>)"
                      value={s.targets_def.targets}
                      onApply={(next) => setAny("targets_def.targets", next)}
                      rows={16}
                    />
                  </SectionGroup>
                </Stack>
              </SectionGroup>
            </Stack>
          </Collapsible>
        </Stack>
      </CardContent>
    </Card>
  );
}