import React, { useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/Card";
import { Stack } from "../../../components/layout/Stack";
import { Grid } from "../../../components/layout/Grid";
import { Collapsible } from "../../../components/ui/Collapsible";
import type { RunCreationState } from "../state/useRunCreationState";

type EngineKey = "root";

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

function FieldRow(props: {
  label: string;
  children: React.ReactNode;
}) {
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

function NumberInput(props: {
  value: number;
  onChange: (v: number) => void;
}) {
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

export function RootEngineSection({
  runCreation,
}: {
  runCreation: RunCreationState;
}) {
  const { pipelineParametersV1, setEngineField } = runCreation;
  const root = pipelineParametersV1.engines.root;

  const setText = useCallback(
    (path: string, v: string) => setEngineField("root" as EngineKey, path, v),
    [setEngineField]
  );
  const setNum = useCallback(
    (path: string, v: number) => setEngineField("root" as EngineKey, path, v),
    [setEngineField]
  );
  const setBool = useCallback(
    (path: string, v: boolean) => setEngineField("root" as EngineKey, path, v),
    [setEngineField]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Root Engine</CardTitle>
      </CardHeader>

      <CardContent>
        <Stack gap={16}>
          <div className="subtle">
            Core settings are visible first. Advanced engine configuration is available below when needed.
          </div>

          <Collapsible
            title="Core settings"
            subtitle="Common root engine configuration"
            defaultOpen={true}
          >
            <Stack gap={16}>
              <SectionGroup
                title="Engine"
                subtitle="root.engine"
                defaultOpen
              >
                <Grid columns="1fr 1fr 1fr" gap={16}>
                  <FieldRow label="Mode">
                    <TextInput
                      value={root.engine.mode ?? ""}
                      onChange={(v) => setText("engine.mode", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Data path">
                    <TextInput
                      value={root.engine.data_path ?? ""}
                      onChange={(v) => setText("engine.data_path", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Version">
                    <TextInput
                      value={root.engine.version ?? ""}
                      onChange={(v) => setText("engine.version", v)}
                    />
                  </FieldRow>
                </Grid>
              </SectionGroup>

              <SectionGroup
                title="Rotations"
                subtitle="root.rotations"
                defaultOpen={false}
              >
                <Grid columns="1fr 1fr 1fr" gap={16}>
                  <FieldRow label="Rotation method">
                    <TextInput
                      value={root.rotations.rotation_method ?? ""}
                      onChange={(v) => setText("rotations.rotation_method", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Merge same direction">
                    <BoolInput
                      checked={Boolean(root.rotations.merge_same_direction)}
                      onChange={(v) => setBool("rotations.merge_same_direction", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Whipsaw bars">
                    <NumberInput
                      value={Number(root.rotations.whipsaw_bars)}
                      onChange={(v) => setNum("rotations.whipsaw_bars", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Minimum rotation bars">
                    <NumberInput
                      value={Number(root.rotations.min_rotation_bars)}
                      onChange={(v) => setNum("rotations.min_rotation_bars", v)}
                    />
                  </FieldRow>
                  

                  <FieldRow label="Min rotation amplitude">
                    <NumberInput
                      value={Number(root.rotations.min_rotation_amplitude)}
                      onChange={(v) => setNum("rotations.min_rotation_amplitude", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Min rotation amplitude micro">
                    <NumberInput
                      value={Number(root.rotations.min_rotation_amplitude_micro)}
                      onChange={(v) =>
                        setNum("rotations.min_rotation_amplitude_micro", v)
                      }
                    />
                  </FieldRow>
                  <FieldRow label="Min standard amplitude (ticks)">
                    <NumberInput
                      value={Number(root.rotations.min_rotation_amplitude_standard)}
                      onChange={(v) =>
                        setNum("rotations.min_rotation_amplitude_standard", v)
                      }
                    />
                  </FieldRow>

                  <FieldRow label="Min structural amplitude (ticks)">
                    <NumberInput
                      value={Number(root.rotations.min_rotation_amplitude_structural)}
                      onChange={(v) =>
                        setNum("rotations.min_rotation_amplitude_structural", v)
                      }
                    />
                  </FieldRow>
                  <FieldRow label="Max asymmetry (%)">
                    <NumberInput
                      value={Number(root.rotations.max_rotation_asymmetry_pct)}
                      onChange={(v) =>
                        setNum("rotations.max_rotation_asymmetry_pct", v)
                      }
                    />
                  </FieldRow>
                  <FieldRow label="Amplitude tolerance (ticks)">
                    <NumberInput
                      value={Number(root.rotations.rotation_amplitude_tolerance)}
                      onChange={(v) =>
                        setNum("rotations.rotation_amplitude_tolerance", v)
                      }
                    />
                  </FieldRow>
                </Grid>
              </SectionGroup>

              <SectionGroup
                title="Duration"
                subtitle="root.duration"
                defaultOpen={false}
              >
                <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                  <FieldRow label="Min micro bars">
                    <NumberInput
                      value={Number(root.duration.min_bars_micro)}
                      onChange={(v) => setNum("duration.min_bars_micro", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Min standard bars">
                    <NumberInput
                      value={Number(root.duration.min_bars_standard)}
                      onChange={(v) => setNum("duration.min_bars_standard", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Min structural bars">
                    <NumberInput
                      value={Number(root.duration.min_bars_structural)}
                      onChange={(v) => setNum("duration.min_bars_structural", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Max balance bars">
                    <NumberInput
                      value={Number(root.duration.max_bars_balance)}
                      onChange={(v) => setNum("duration.max_bars_balance", v)}
                    />
                  </FieldRow>

                  <FieldRow label="Ignore time gaps">
                    <BoolInput
                      checked={Boolean(root.duration.ignore_time_gaps)}
                      onChange={(v) => setBool("duration.ignore_time_gaps", v)}
                    />
                  </FieldRow>
                </Grid>
              </SectionGroup>

              <SectionGroup
                title="Volume"
                subtitle="root.volume"
                defaultOpen={false}
              >
                <Grid columns="1fr 1fr 1fr" gap={16}>
                  <FieldRow label="Distribution type">
                    <TextInput
                      value={root.volume.volume_distribution_type ?? ""}
                      onChange={(v) =>
                        setText("volume.volume_distribution_type", v)
                      }
                    />
                  </FieldRow>
                  <FieldRow label="Min HVN/LVN ratio">
                    <NumberInput
                      value={Number(root.volume.hvn_lvn_ratio_min)}
                      onChange={(v) => setNum("volume.hvn_lvn_ratio_min", v)}
                    />
                  </FieldRow>
                  <FieldRow label="Min internal volume (%)">
                    <NumberInput
                      value={Number(root.volume.min_internal_volume_pct)}
                      onChange={(v) => setNum("volume.min_internal_volume_pct", v)}
                    />
                  </FieldRow>
                </Grid>
              </SectionGroup>

              <SectionGroup
                title="Delta"
                subtitle="root.delta"
                defaultOpen={false}
              >
                <Grid columns="1fr 1fr 1fr" gap={16}>
                  <FieldRow label="Max delta fraction">
                    <NumberInput
                      value={Number(root.delta.delta_max_fraction_volume)}
                      onChange={(v) =>
                        setNum("delta.delta_max_fraction_volume", v)
                      }
                    />
                  </FieldRow>
                  <FieldRow label="Require alternation">
                    <BoolInput
                      checked={Boolean(root.delta.delta_rotation_alternation_required)}
                      onChange={(v) =>
                        setBool("delta.delta_rotation_alternation_required", v)
                      }
                    />
                  </FieldRow>
                  <FieldRow label="Aggressive volume threshold">
                    <NumberInput
                      value={Number(root.delta.aggressive_volume_threshold)}
                      onChange={(v) =>
                        setNum("delta.aggressive_volume_threshold", v)
                      }
                    />
                  </FieldRow>
                </Grid>
              </SectionGroup>
            </Stack>
          </Collapsible>

          <Collapsible
            title="Advanced settings"
            subtitle="Balance, breakout, export and session-level configuration"
            defaultOpen={false}
          >
            <Stack gap={16}>
              <SectionGroup
                title="Balance"
                subtitle="root.balance"
                defaultOpen={false}
              >
                <Stack gap={16}>
                  <Grid columns="1fr 1fr 1fr 1fr 1fr" gap={16}>
                    <FieldRow label="balance.min_rotations">
                      <NumberInput
                        value={Number(root.balance.min_rotations)}
                        onChange={(v) => setNum("balance.min_rotations", v)}
                      />
                    </FieldRow>
                    <FieldRow label="balance.max_gap_bars">
                      <NumberInput
                        value={Number(root.balance.max_gap_bars)}
                        onChange={(v) => setNum("balance.max_gap_bars", v)}
                      />
                    </FieldRow>
                    <FieldRow label="balance.min_bars">
                      <NumberInput
                        value={Number(root.balance.min_bars)}
                        onChange={(v) => setNum("balance.min_bars", v)}
                      />
                    </FieldRow>
                    <FieldRow label="balance.min_width">
                      <NumberInput
                        value={Number(root.balance.min_width)}
                        onChange={(v) => setNum("balance.min_width", v)}
                      />
                    </FieldRow>
                    <FieldRow label="balance.max_width">
                      <NumberInput
                        value={Number(root.balance.max_width)}
                        onChange={(v) => setNum("balance.max_width", v)}
                      />
                    </FieldRow>
                  </Grid>

                  <SectionGroup
                    title="Balance volume profile"
                    subtitle="root.balance.volume_profile"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr 1fr 1fr 1fr" gap={16}>
                      <FieldRow label="balance.volume_profile.min_total_volume">
                        <NumberInput
                          value={Number(root.balance.volume_profile.min_total_volume)}
                          onChange={(v) =>
                            setNum("balance.volume_profile.min_total_volume", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.volume_profile.bin_size">
                        <NumberInput
                          value={Number(root.balance.volume_profile.bin_size)}
                          onChange={(v) =>
                            setNum("balance.volume_profile.bin_size", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.volume_profile.hvn_threshold_factor">
                        <NumberInput
                          value={Number(
                            root.balance.volume_profile.hvn_threshold_factor
                          )}
                          onChange={(v) =>
                            setNum("balance.volume_profile.hvn_threshold_factor", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.volume_profile.lvn_threshold_factor">
                        <NumberInput
                          value={Number(
                            root.balance.volume_profile.lvn_threshold_factor
                          )}
                          onChange={(v) =>
                            setNum("balance.volume_profile.lvn_threshold_factor", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.volume_profile.window_around_poc">
                        <NumberInput
                          value={Number(
                            root.balance.volume_profile.window_around_poc
                          )}
                          onChange={(v) =>
                            setNum("balance.volume_profile.window_around_poc", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.volume_profile.window_around_mid">
                        <NumberInput
                          value={Number(
                            root.balance.volume_profile.window_around_mid
                          )}
                          onChange={(v) =>
                            setNum("balance.volume_profile.window_around_mid", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Balance classification"
                    subtitle="root.balance.classification"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                      <FieldRow label="balance.classification.compressed_width_factor">
                        <NumberInput
                          value={Number(
                            root.balance.classification.compressed_width_factor
                          )}
                          onChange={(v) =>
                            setNum(
                              "balance.classification.compressed_width_factor",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.classification.wide_width_factor">
                        <NumberInput
                          value={Number(
                            root.balance.classification.wide_width_factor
                          )}
                          onChange={(v) =>
                            setNum("balance.classification.wide_width_factor", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.classification.asymmetry_threshold">
                        <NumberInput
                          value={Number(
                            root.balance.classification.asymmetry_threshold
                          )}
                          onChange={(v) =>
                            setNum("balance.classification.asymmetry_threshold", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.classification.center_volume_threshold">
                        <NumberInput
                          value={Number(
                            root.balance.classification.center_volume_threshold
                          )}
                          onChange={(v) =>
                            setNum(
                              "balance.classification.center_volume_threshold",
                              v
                            )
                          }
                        />
                      </FieldRow>

                      <FieldRow label="balance.classification.edge_volume_threshold">
                        <NumberInput
                          value={Number(
                            root.balance.classification.edge_volume_threshold
                          )}
                          onChange={(v) =>
                            setNum("balance.classification.edge_volume_threshold", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.classification.hvn_density_threshold">
                        <NumberInput
                          value={Number(
                            root.balance.classification.hvn_density_threshold
                          )}
                          onChange={(v) =>
                            setNum("balance.classification.hvn_density_threshold", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.classification.lvn_density_threshold">
                        <NumberInput
                          value={Number(
                            root.balance.classification.lvn_density_threshold
                          )}
                          onChange={(v) =>
                            setNum("balance.classification.lvn_density_threshold", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="balance.classification.equilibrium_score">
                        <NumberInput
                          value={Number(
                            root.balance.classification.equilibrium_score
                          )}
                          onChange={(v) =>
                            setNum("balance.classification.equilibrium_score", v)
                          }
                        />
                      </FieldRow>
                    </Grid>

                    <SectionGroup
                      title="Classification weights"
                      subtitle="root.balance.classification.weights"
                      defaultOpen={false}
                    >
                      <Grid columns="1fr 1fr 1fr 1fr 1fr 1fr" gap={16}>
                        <FieldRow label="balance.classification.w_width">
                          <NumberInput
                            value={Number(root.balance.classification.w_width)}
                            onChange={(v) =>
                              setNum("balance.classification.w_width", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="balance.classification.w_asymmetry">
                          <NumberInput
                            value={Number(root.balance.classification.w_asymmetry)}
                            onChange={(v) =>
                              setNum("balance.classification.w_asymmetry", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="balance.classification.w_center_volume">
                          <NumberInput
                            value={Number(
                              root.balance.classification.w_center_volume
                            )}
                            onChange={(v) =>
                              setNum("balance.classification.w_center_volume", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="balance.classification.w_hvn_density">
                          <NumberInput
                            value={Number(root.balance.classification.w_hvn_density)}
                            onChange={(v) =>
                              setNum("balance.classification.w_hvn_density", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="balance.classification.w_lvn_density">
                          <NumberInput
                            value={Number(root.balance.classification.w_lvn_density)}
                            onChange={(v) =>
                              setNum("balance.classification.w_lvn_density", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="balance.classification.w_edge_volume">
                          <NumberInput
                            value={Number(root.balance.classification.w_edge_volume)}
                            onChange={(v) =>
                              setNum("balance.classification.w_edge_volume", v)
                            }
                          />
                        </FieldRow>
                      </Grid>
                    </SectionGroup>

                    <SectionGroup
                      title="Classification refs"
                      subtitle="root.balance.classification.refs"
                      defaultOpen={false}
                    >
                      <Grid columns="1fr 1fr 1fr 1fr 1fr 1fr" gap={16}>
                        <FieldRow label="balance.classification.asymmetry_ref">
                          <NumberInput
                            value={Number(
                              root.balance.classification.asymmetry_ref
                            )}
                            onChange={(v) =>
                              setNum("balance.classification.asymmetry_ref", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="balance.classification.center_volume_ref">
                          <NumberInput
                            value={Number(
                              root.balance.classification.center_volume_ref
                            )}
                            onChange={(v) =>
                              setNum("balance.classification.center_volume_ref", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="balance.classification.hvn_density_ref">
                          <NumberInput
                            value={Number(
                              root.balance.classification.hvn_density_ref
                            )}
                            onChange={(v) =>
                              setNum("balance.classification.hvn_density_ref", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="balance.classification.lvn_density_ref">
                          <NumberInput
                            value={Number(
                              root.balance.classification.lvn_density_ref
                            )}
                            onChange={(v) =>
                              setNum("balance.classification.lvn_density_ref", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="balance.classification.edge_volume_ref">
                          <NumberInput
                            value={Number(
                              root.balance.classification.edge_volume_ref
                            )}
                            onChange={(v) =>
                              setNum("balance.classification.edge_volume_ref", v)
                            }
                          />
                        </FieldRow>
                      </Grid>
                    </SectionGroup>
                  </SectionGroup>
                </Stack>
              </SectionGroup>

              <SectionGroup
                title="Breakout"
                subtitle="root.breakout"
                defaultOpen={false}
              >
                <Stack gap={16}>
                  <SectionGroup
                    title="Early detection"
                    subtitle="root.breakout.early_detection"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.early_detection.enabled">
                        <BoolInput
                          checked={Boolean(root.breakout.early_detection.enabled)}
                          onChange={(v) =>
                            setBool("breakout.early_detection.enabled", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.early_detection.lower_timeframe">
                        <TextInput
                          value={root.breakout.early_detection.lower_timeframe ?? ""}
                          onChange={(v) =>
                            setText("breakout.early_detection.lower_timeframe", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.early_detection.reference_timeframe">
                        <TextInput
                          value={
                            root.breakout.early_detection.reference_timeframe ?? ""
                          }
                          onChange={(v) =>
                            setText(
                              "breakout.early_detection.reference_timeframe",
                              v
                            )
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Pre-breakout"
                    subtitle="root.breakout.pre_breakout"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.pre_breakout.enabled">
                        <BoolInput
                          checked={Boolean(root.breakout.pre_breakout.enabled)}
                          onChange={(v) =>
                            setBool("breakout.pre_breakout.enabled", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.pre_breakout.volatility_window">
                        <NumberInput
                          value={Number(root.breakout.pre_breakout.volatility_window)}
                          onChange={(v) =>
                            setNum("breakout.pre_breakout.volatility_window", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.pre_breakout.min_volatility_increase">
                        <NumberInput
                          value={Number(
                            root.breakout.pre_breakout.min_volatility_increase
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.pre_breakout.min_volatility_increase",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.pre_breakout.max_lvn_distance">
                        <NumberInput
                          value={Number(root.breakout.pre_breakout.max_lvn_distance)}
                          onChange={(v) =>
                            setNum("breakout.pre_breakout.max_lvn_distance", v)
                          }
                        />
                      </FieldRow>

                      <FieldRow label="breakout.pre_breakout.min_delta_bias">
                        <NumberInput
                          value={Number(root.breakout.pre_breakout.min_delta_bias)}
                          onChange={(v) =>
                            setNum("breakout.pre_breakout.min_delta_bias", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.pre_breakout.boundary_volume_factor">
                        <NumberInput
                          value={Number(
                            root.breakout.pre_breakout.boundary_volume_factor
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.pre_breakout.boundary_volume_factor",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.pre_breakout.min_score">
                        <NumberInput
                          value={Number(root.breakout.pre_breakout.min_score)}
                          onChange={(v) =>
                            setNum("breakout.pre_breakout.min_score", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.pre_breakout.max_lead_minutes">
                        <NumberInput
                          value={Number(root.breakout.pre_breakout.max_lead_minutes)}
                          onChange={(v) =>
                            setNum("breakout.pre_breakout.max_lead_minutes", v)
                          }
                        />
                      </FieldRow>
                    </Grid>

                    <SectionGroup
                      title="Pre-breakout weights"
                      subtitle="root.breakout.pre_breakout.weights"
                      defaultOpen={false}
                    >
                      <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                        <FieldRow label="breakout.pre_breakout.weights.compression">
                          <NumberInput
                            value={Number(
                              root.breakout.pre_breakout.weights.compression
                            )}
                            onChange={(v) =>
                              setNum("breakout.pre_breakout.weights.compression", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="breakout.pre_breakout.weights.lvn_proximity">
                          <NumberInput
                            value={Number(
                              root.breakout.pre_breakout.weights.lvn_proximity
                            )}
                            onChange={(v) =>
                              setNum(
                                "breakout.pre_breakout.weights.lvn_proximity",
                                v
                              )
                            }
                          />
                        </FieldRow>
                        <FieldRow label="breakout.pre_breakout.weights.volatility">
                          <NumberInput
                            value={Number(
                              root.breakout.pre_breakout.weights.volatility
                            )}
                            onChange={(v) =>
                              setNum("breakout.pre_breakout.weights.volatility", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="breakout.pre_breakout.weights.delta_bias">
                          <NumberInput
                            value={Number(
                              root.breakout.pre_breakout.weights.delta_bias
                            )}
                            onChange={(v) =>
                              setNum("breakout.pre_breakout.weights.delta_bias", v)
                            }
                          />
                        </FieldRow>
                      </Grid>
                    </SectionGroup>

                    <SectionGroup
                      title="Pre-breakout trigger"
                      subtitle="root.breakout.pre_breakout.trigger"
                      defaultOpen={false}
                    >
                      <Grid columns="1fr 1fr 1fr" gap={16}>
                        <FieldRow label="breakout.pre_breakout.trigger.type">
                          <TextInput
                            value={root.breakout.pre_breakout.trigger.type ?? ""}
                            onChange={(v) =>
                              setText("breakout.pre_breakout.trigger.type", v)
                            }
                          />
                        </FieldRow>
                        <FieldRow label="breakout.pre_breakout.trigger.min_consecutive">
                          <NumberInput
                            value={Number(
                              root.breakout.pre_breakout.trigger.min_consecutive
                            )}
                            onChange={(v) =>
                              setNum(
                                "breakout.pre_breakout.trigger.min_consecutive",
                                v
                              )
                            }
                          />
                        </FieldRow>
                        <FieldRow label="breakout.pre_breakout.trigger.min_penetration">
                          <NumberInput
                            value={Number(
                              root.breakout.pre_breakout.trigger.min_penetration
                            )}
                            onChange={(v) =>
                              setNum(
                                "breakout.pre_breakout.trigger.min_penetration",
                                v
                              )
                            }
                          />
                        </FieldRow>
                      </Grid>
                    </SectionGroup>

                    <SectionGroup
                      title="Pre-breakout filters"
                      subtitle="root.breakout.pre_breakout.filters"
                      defaultOpen={false}
                    >
                      <Grid columns="1fr 1fr" gap={16}>
                        <FieldRow label="breakout.pre_breakout.filters.min_volume_ratio">
                          <NumberInput
                            value={Number(
                              root.breakout.pre_breakout.filters.min_volume_ratio
                            )}
                            onChange={(v) =>
                              setNum(
                                "breakout.pre_breakout.filters.min_volume_ratio",
                                v
                              )
                            }
                          />
                        </FieldRow>
                        <FieldRow label="breakout.pre_breakout.filters.min_volatility_ratio">
                          <NumberInput
                            value={Number(
                              root.breakout.pre_breakout.filters.min_volatility_ratio
                            )}
                            onChange={(v) =>
                              setNum(
                                "breakout.pre_breakout.filters.min_volatility_ratio",
                                v
                              )
                            }
                          />
                        </FieldRow>
                      </Grid>
                    </SectionGroup>
                  </SectionGroup>

                  <Grid columns="1fr 1fr 1fr" gap={16}>
                    <FieldRow label="breakout.mode">
                      <TextInput
                        value={root.breakout.mode ?? ""}
                        onChange={(v) => setText("breakout.mode", v)}
                      />
                    </FieldRow>
                    <FieldRow label="breakout.post_balance_bars">
                      <NumberInput
                        value={Number(root.breakout.post_balance_bars)}
                        onChange={(v) =>
                          setNum("breakout.post_balance_bars", v)
                        }
                      />
                    </FieldRow>
                    <FieldRow label="breakout.breakout_body_margin">
                      <NumberInput
                        value={Number(root.breakout.breakout_body_margin)}
                        onChange={(v) =>
                          setNum("breakout.breakout_body_margin", v)
                        }
                      />
                    </FieldRow>
                  </Grid>

                  <SectionGroup
                    title="Hybrid"
                    subtitle="root.breakout.hybrid"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr" gap={16}>
                      <FieldRow label="breakout.hybrid.body_ratio_required">
                        <NumberInput
                          value={Number(root.breakout.hybrid.body_ratio_required)}
                          onChange={(v) =>
                            setNum("breakout.hybrid.body_ratio_required", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.hybrid.use_previous_body">
                        <BoolInput
                          checked={Boolean(root.breakout.hybrid.use_previous_body)}
                          onChange={(v) =>
                            setBool("breakout.hybrid.use_previous_body", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Confirmation"
                    subtitle="root.breakout.confirmation"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.confirmation.enabled">
                        <BoolInput
                          checked={Boolean(root.breakout.confirmation.enabled)}
                          onChange={(v) =>
                            setBool("breakout.confirmation.enabled", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.confirmation.max_bars">
                        <NumberInput
                          value={Number(root.breakout.confirmation.max_bars)}
                          onChange={(v) =>
                            setNum("breakout.confirmation.max_bars", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.confirmation.closes_required">
                        <NumberInput
                          value={Number(root.breakout.confirmation.closes_required)}
                          onChange={(v) =>
                            setNum("breakout.confirmation.closes_required", v)
                          }
                        />
                      </FieldRow>

                      <FieldRow label="breakout.confirmation.volume_confirmation">
                        <BoolInput
                          checked={Boolean(
                            root.breakout.confirmation.volume_confirmation
                          )}
                          onChange={(v) =>
                            setBool("breakout.confirmation.volume_confirmation", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.confirmation.delta_confirmation">
                        <BoolInput
                          checked={Boolean(
                            root.breakout.confirmation.delta_confirmation
                          )}
                          onChange={(v) =>
                            setBool("breakout.confirmation.delta_confirmation", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.confirmation.delta_min_abs">
                        <NumberInput
                          value={Number(root.breakout.confirmation.delta_min_abs)}
                          onChange={(v) =>
                            setNum("breakout.confirmation.delta_min_abs", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Classification"
                    subtitle="root.breakout.classification"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.classification.max_reentry_fraction">
                        <NumberInput
                          value={Number(
                            root.breakout.classification.max_reentry_fraction
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.classification.max_reentry_fraction",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.classification.failed_max_bars">
                        <NumberInput
                          value={Number(
                            root.breakout.classification.failed_max_bars
                          )}
                          onChange={(v) =>
                            setNum("breakout.classification.failed_max_bars", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.classification.retest_tolerance">
                        <NumberInput
                          value={Number(
                            root.breakout.classification.retest_tolerance
                          )}
                          onChange={(v) =>
                            setNum("breakout.classification.retest_tolerance", v)
                          }
                        />
                      </FieldRow>

                      <FieldRow label="breakout.classification.retest_min_hold_bars">
                        <NumberInput
                          value={Number(
                            root.breakout.classification.retest_min_hold_bars
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.classification.retest_min_hold_bars",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.classification.dirty_wick_fraction">
                        <NumberInput
                          value={Number(
                            root.breakout.classification.dirty_wick_fraction
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.classification.dirty_wick_fraction",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.classification.min_follow_through">
                        <NumberInput
                          value={Number(
                            root.breakout.classification.min_follow_through
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.classification.min_follow_through",
                              v
                            )
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Classification labels"
                    subtitle="root.breakout.classification_labels"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.classification_labels.dirty_if_wick_fraction_above">
                        <NumberInput
                          value={Number(
                            root.breakout.classification_labels
                              .dirty_if_wick_fraction_above
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.classification_labels.dirty_if_wick_fraction_above",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.classification_labels.failed_if_no_follow_after_bars">
                        <NumberInput
                          value={Number(
                            root.breakout.classification_labels
                              .failed_if_no_follow_after_bars
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.classification_labels.failed_if_no_follow_after_bars",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.classification_labels.clean_if_follow_through_above">
                        <NumberInput
                          value={Number(
                            root.breakout.classification_labels
                              .clean_if_follow_through_above
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.classification_labels.clean_if_follow_through_above",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.classification_labels.retest_if_pullback_with_hold">
                        <NumberInput
                          value={Number(
                            root.breakout.classification_labels
                              .retest_if_pullback_with_hold
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.classification_labels.retest_if_pullback_with_hold",
                              v
                            )
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Strength"
                    subtitle="root.breakout.strength"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.strength.momentum_weight">
                        <NumberInput
                          value={Number(root.breakout.strength.momentum_weight)}
                          onChange={(v) =>
                            setNum("breakout.strength.momentum_weight", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.strength.delta_weight">
                        <NumberInput
                          value={Number(root.breakout.strength.delta_weight)}
                          onChange={(v) =>
                            setNum("breakout.strength.delta_weight", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.strength.volume_spike_weight">
                        <NumberInput
                          value={Number(root.breakout.strength.volume_spike_weight)}
                          onChange={(v) =>
                            setNum("breakout.strength.volume_spike_weight", v)
                          }
                        />
                      </FieldRow>

                      <FieldRow label="breakout.strength.volatility_weight">
                        <NumberInput
                          value={Number(root.breakout.strength.volatility_weight)}
                          onChange={(v) =>
                            setNum("breakout.strength.volatility_weight", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.strength.distance_from_vpoc_weight">
                        <NumberInput
                          value={Number(
                            root.breakout.strength.distance_from_vpoc_weight
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.strength.distance_from_vpoc_weight",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.strength.hvn_lvn_break_weight">
                        <NumberInput
                          value={Number(
                            root.breakout.strength.hvn_lvn_break_weight
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.strength.hvn_lvn_break_weight",
                              v
                            )
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Strength normalization"
                    subtitle="root.breakout.strength_normalization"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.strength_normalization.enabled">
                        <BoolInput
                          checked={Boolean(
                            root.breakout.strength_normalization.enabled
                          )}
                          onChange={(v) =>
                            setBool(
                              "breakout.strength_normalization.enabled",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.strength_normalization.method">
                        <TextInput
                          value={root.breakout.strength_normalization.method ?? ""}
                          onChange={(v) =>
                            setText("breakout.strength_normalization.method", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.strength_normalization.min_raw">
                        <NumberInput
                          value={Number(
                            root.breakout.strength_normalization.min_raw
                          )}
                          onChange={(v) =>
                            setNum("breakout.strength_normalization.min_raw", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.strength_normalization.max_raw">
                        <NumberInput
                          value={Number(
                            root.breakout.strength_normalization.max_raw
                          )}
                          onChange={(v) =>
                            setNum("breakout.strength_normalization.max_raw", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.strength_normalization.sigmoid_k">
                        <NumberInput
                          value={Number(
                            root.breakout.strength_normalization.sigmoid_k
                          )}
                          onChange={(v) =>
                            setNum("breakout.strength_normalization.sigmoid_k", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="ATR"
                    subtitle="root.breakout.atr"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.atr.enabled">
                        <BoolInput
                          checked={Boolean(root.breakout.atr.enabled)}
                          onChange={(v) => setBool("breakout.atr.enabled", v)}
                        />
                      </FieldRow>
                      <FieldRow label="breakout.atr.period">
                        <NumberInput
                          value={Number(root.breakout.atr.period)}
                          onChange={(v) => setNum("breakout.atr.period", v)}
                        />
                      </FieldRow>
                      <FieldRow label="breakout.atr.use_for_strength">
                        <BoolInput
                          checked={Boolean(root.breakout.atr.use_for_strength)}
                          onChange={(v) =>
                            setBool("breakout.atr.use_for_strength", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.atr.normalization_factor">
                        <NumberInput
                          value={Number(root.breakout.atr.normalization_factor)}
                          onChange={(v) =>
                            setNum("breakout.atr.normalization_factor", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Volatility filter"
                    subtitle="root.breakout.volatility_filter"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.volatility_filter.enable_filter">
                        <BoolInput
                          checked={Boolean(
                            root.breakout.volatility_filter.enable_filter
                          )}
                          onChange={(v) =>
                            setBool("breakout.volatility_filter.enable_filter", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.volatility_filter.min_compression_ratio">
                        <NumberInput
                          value={Number(
                            root.breakout.volatility_filter.min_compression_ratio
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.volatility_filter.min_compression_ratio",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.volatility_filter.max_compression_ratio">
                        <NumberInput
                          value={Number(
                            root.breakout.volatility_filter.max_compression_ratio
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.volatility_filter.max_compression_ratio",
                              v
                            )
                          }
                        />
                      </FieldRow>

                      <FieldRow label="breakout.volatility_filter.min_stability_score">
                        <NumberInput
                          value={Number(
                            root.breakout.volatility_filter.min_stability_score
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.volatility_filter.min_stability_score",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.volatility_filter.soft_penalty">
                        <NumberInput
                          value={Number(
                            root.breakout.volatility_filter.soft_penalty
                          )}
                          onChange={(v) =>
                            setNum("breakout.volatility_filter.soft_penalty", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Follow-through"
                    subtitle="root.breakout.follow_through"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                      <FieldRow label="breakout.follow_through.observation_bars">
                        <NumberInput
                          value={Number(
                            root.breakout.follow_through.observation_bars
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.follow_through.observation_bars",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.follow_through.retracement_factor">
                        <NumberInput
                          value={Number(
                            root.breakout.follow_through.retracement_factor
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.follow_through.retracement_factor",
                              v
                            )
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.follow_through.retest_window">
                        <NumberInput
                          value={Number(
                            root.breakout.follow_through.retest_window
                          )}
                          onChange={(v) =>
                            setNum("breakout.follow_through.retest_window", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.follow_through.boundary_hold_bars">
                        <NumberInput
                          value={Number(
                            root.breakout.follow_through.boundary_hold_bars
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.follow_through.boundary_hold_bars",
                              v
                            )
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Rotations filter"
                    subtitle="root.breakout.rotations_filter"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr" gap={16}>
                      <FieldRow label="breakout.rotations_filter.min_rotations">
                        <NumberInput
                          value={Number(
                            root.breakout.rotations_filter.min_rotations
                          )}
                          onChange={(v) =>
                            setNum("breakout.rotations_filter.min_rotations", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="breakout.rotations_filter.min_directional_bias">
                        <NumberInput
                          value={Number(
                            root.breakout.rotations_filter.min_directional_bias
                          )}
                          onChange={(v) =>
                            setNum(
                              "breakout.rotations_filter.min_directional_bias",
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
                title="Breakout ranking"
                subtitle="root.breakout_ranking"
                defaultOpen={false}
              >
                <Grid columns="1fr 1fr 1fr 1fr" gap={16}>
                  <FieldRow label="breakout_ranking.enabled">
                    <BoolInput
                      checked={Boolean(root.breakout_ranking.enabled)}
                      onChange={(v) =>
                        setBool("breakout_ranking.enabled", v)
                      }
                    />
                  </FieldRow>
                  <FieldRow label="breakout_ranking.use_normalized">
                    <BoolInput
                      checked={Boolean(root.breakout_ranking.use_normalized)}
                      onChange={(v) =>
                        setBool("breakout_ranking.use_normalized", v)
                      }
                    />
                  </FieldRow>
                  <FieldRow label="breakout_ranking.top_n">
                    <NumberInput
                      value={Number(root.breakout_ranking.top_n)}
                      onChange={(v) => setNum("breakout_ranking.top_n", v)}
                    />
                  </FieldRow>
                  <FieldRow label="breakout_ranking.group_by_session">
                    <BoolInput
                      checked={Boolean(root.breakout_ranking.group_by_session)}
                      onChange={(v) =>
                        setBool("breakout_ranking.group_by_session", v)
                      }
                    />
                  </FieldRow>
                </Grid>
              </SectionGroup>

              <SectionGroup
                title="Export"
                subtitle="root.export"
                defaultOpen={false}
              >
                <Grid columns="1fr 1fr 1fr" gap={16}>
                  <FieldRow label="export.enabled">
                    <BoolInput
                      checked={Boolean(root.export.enabled)}
                      onChange={(v) => setBool("export.enabled", v)}
                    />
                  </FieldRow>
                  <FieldRow label="export.format">
                    <TextInput
                      value={root.export.format ?? ""}
                      onChange={(v) => setText("export.format", v)}
                    />
                  </FieldRow>
                  <FieldRow label="export.output_dir">
                    <TextInput
                      value={root.export.output_dir ?? ""}
                      onChange={(v) => setText("export.output_dir", v)}
                    />
                  </FieldRow>

                  <FieldRow label="export.filename_prefix">
                    <TextInput
                      value={root.export.filename_prefix ?? ""}
                      onChange={(v) => setText("export.filename_prefix", v)}
                    />
                  </FieldRow>
                  <FieldRow label="export.include_timestamp">
                    <BoolInput
                      checked={Boolean(root.export.include_timestamp)}
                      onChange={(v) =>
                        setBool("export.include_timestamp", v)
                      }
                    />
                  </FieldRow>
                </Grid>
              </SectionGroup>

              <SectionGroup
                title="Session levels"
                subtitle="root.session_levels"
                defaultOpen={false}
              >
                <Stack gap={16}>
                  <Grid columns="1fr" gap={16}>
                    <FieldRow label="session_levels.version">
                      <TextInput
                        value={root.session_levels.version ?? ""}
                        onChange={(v) =>
                          setText("session_levels.version", v)
                        }
                      />
                    </FieldRow>
                  </Grid>

                  <SectionGroup
                    title="Sessions"
                    subtitle="root.session_levels.sessions"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr" gap={16}>
                      <FieldRow label="session_levels.sessions.asia.open">
                        <TextInput
                          value={root.session_levels.sessions.asia.open ?? ""}
                          onChange={(v) =>
                            setText("session_levels.sessions.asia.open", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="session_levels.sessions.asia.close">
                        <TextInput
                          value={root.session_levels.sessions.asia.close ?? ""}
                          onChange={(v) =>
                            setText("session_levels.sessions.asia.close", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="session_levels.sessions.asia.timezone">
                        <TextInput
                          value={root.session_levels.sessions.asia.timezone ?? ""}
                          onChange={(v) =>
                            setText("session_levels.sessions.asia.timezone", v)
                          }
                        />
                      </FieldRow>

                      <FieldRow label="session_levels.sessions.europe.open">
                        <TextInput
                          value={root.session_levels.sessions.europe.open ?? ""}
                          onChange={(v) =>
                            setText("session_levels.sessions.europe.open", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="session_levels.sessions.europe.close">
                        <TextInput
                          value={root.session_levels.sessions.europe.close ?? ""}
                          onChange={(v) =>
                            setText("session_levels.sessions.europe.close", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="session_levels.sessions.europe.timezone">
                        <TextInput
                          value={
                            root.session_levels.sessions.europe.timezone ?? ""
                          }
                          onChange={(v) =>
                            setText("session_levels.sessions.europe.timezone", v)
                          }
                        />
                      </FieldRow>

                      <FieldRow label="session_levels.sessions.usa.open">
                        <TextInput
                          value={root.session_levels.sessions.usa.open ?? ""}
                          onChange={(v) =>
                            setText("session_levels.sessions.usa.open", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="session_levels.sessions.usa.close">
                        <TextInput
                          value={root.session_levels.sessions.usa.close ?? ""}
                          onChange={(v) =>
                            setText("session_levels.sessions.usa.close", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="session_levels.sessions.usa.timezone">
                        <TextInput
                          value={root.session_levels.sessions.usa.timezone ?? ""}
                          onChange={(v) =>
                            setText("session_levels.sessions.usa.timezone", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="Volume profile"
                    subtitle="root.session_levels.volume_profile"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr" gap={16}>
                      <FieldRow label="session_levels.volume_profile.bin_size">
                        <NumberInput
                          value={Number(
                            root.session_levels.volume_profile.bin_size
                          )}
                          onChange={(v) =>
                            setNum("session_levels.volume_profile.bin_size", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="session_levels.volume_profile.value_area_pct">
                        <NumberInput
                          value={Number(
                            root.session_levels.volume_profile.value_area_pct
                          )}
                          onChange={(v) =>
                            setNum(
                              "session_levels.volume_profile.value_area_pct",
                              v
                            )
                          }
                        />
                      </FieldRow>
                    </Grid>
                  </SectionGroup>

                  <SectionGroup
                    title="VWAP"
                    subtitle="root.session_levels.vwap"
                    defaultOpen={false}
                  >
                    <FieldRow label="session_levels.vwap.enabled">
                      <BoolInput
                        checked={Boolean(root.session_levels.vwap.enabled)}
                        onChange={(v) =>
                          setBool("session_levels.vwap.enabled", v)
                        }
                      />
                    </FieldRow>
                  </SectionGroup>

                  <SectionGroup
                    title="Session export"
                    subtitle="root.session_levels.export"
                    defaultOpen={false}
                  >
                    <Grid columns="1fr 1fr 1fr" gap={16}>
                      <FieldRow label="session_levels.export.enabled">
                        <BoolInput
                          checked={Boolean(root.session_levels.export.enabled)}
                          onChange={(v) =>
                            setBool("session_levels.export.enabled", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="session_levels.export.output_dir">
                        <TextInput
                          value={root.session_levels.export.output_dir ?? ""}
                          onChange={(v) =>
                            setText("session_levels.export.output_dir", v)
                          }
                        />
                      </FieldRow>
                      <FieldRow label="session_levels.export.filename_prefix">
                        <TextInput
                          value={
                            root.session_levels.export.filename_prefix ?? ""
                          }
                          onChange={(v) =>
                            setText("session_levels.export.filename_prefix", v)
                          }
                        />
                      </FieldRow>
                    </Grid>
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