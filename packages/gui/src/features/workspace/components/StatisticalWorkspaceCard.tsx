import React from "react";
import { useApi } from "../../../api/ApiProvider";
import { createWorkspaceClient } from "../api/workspaceClient";
import type { StatisticalWorkspaceState } from "../model/statisticalWorkspaceState";
import type {
  ArtifactRefInput,
  StatisticalRunRequest,
} from "../model/workspaceTypes";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "../../../components/ui/Card";
import { Stack } from "../../../components/layout/Stack";
import { Grid } from "../../../components/layout/Grid";
import { Button } from "../../../components/ui/Button";
import { Collapsible } from "../../../components/ui/Collapsible";
import { FormField } from "../../../components/ui/FormField";
import { ArtifactRefBadge } from "./ArtifactRefBadge";
import { StepStatusBanner } from "./StepStatusBanner";
import { ArtifactSelector } from "./ArtifactSelector";
import {
  listStatisticalWorkspacePresets,
  saveStatisticalWorkspacePreset,
  loadStatisticalWorkspacePreset,
  deleteStatisticalWorkspacePreset,
  exportStatisticalWorkspacePresetJson,
  importStatisticalWorkspacePresetJson,
} from "../model/statisticalWorkspacePresets";
import { routes } from "../../../app/routes";
import { getBucketLabel } from "../utils/bucketLabels";
import { BucketizersConfig } from "@/features/workspace/model/workspaceTypes";


type StatisticalWorkspaceCardProps = {
  availableRootArtifacts?: ArtifactRefInput[];
  initialRootArtifactRef?: ArtifactRefInput | null;
  onArtifactProduced?: (artifactRef: ArtifactRefInput | null) => void;
};

function parseCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinCsv(values: string[]): string {
  return values.join(", ");
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function readString(value: unknown, fallback: string): string {
  return typeof value === "string" ? value : fallback;
}

function readNumber(value: unknown, fallback: number): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function readBoolean(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function readStringArray(value: unknown, fallback: string[]): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : fallback;
}

function readRange(
  source: Record<string, unknown> | null,
  key: string,
  fallback: [number, number]
): [number, number] {
  const value = source?.[key];
  if (
    Array.isArray(value) &&
    value.length >= 2 &&
    typeof value[0] === "number" &&
    typeof value[1] === "number"
  ) {
    return [value[0], value[1]];
  }
  return fallback;
}

function readTimePair(
  source: Record<string, unknown> | null,
  key: string,
  fallback: [string, string]
): [string, string] {
  const value = source?.[key];
  if (
    Array.isArray(value) &&
    value.length >= 2 &&
    typeof value[0] === "string" &&
    typeof value[1] === "string"
  ) {
    return [value[0], value[1]];
  }
  return fallback;
}

type SemanticSectionProps = {
  title: string;
  subtitle: string;
  badge: "INPUT" | "CORE" | "SECONDARY" | "CLASSIFICATION" | "DEBUG";
  children: React.ReactNode;
};

function SemanticSection({
  title,
  subtitle,
  badge,
  children,
}: SemanticSectionProps) {
  return (
    <section
      style={{
        border: "1px solid var(--border)",
        borderRadius: 14,
        padding: 14,
        background: "var(--surface)",
      }}
    >
      <Stack gap={14}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ fontWeight: 900, fontSize: 15 }}>{title}</div>
            <span
              style={{
                fontSize: 10,
                fontWeight: 800,
                letterSpacing: 0.8,
                opacity: 0.65,
                border: "1px solid var(--border)",
                borderRadius: 999,
                padding: "2px 7px",
              }}
            >
              {badge}
            </span>
          </div>

          <div className="subtle" style={{ marginTop: 4, fontSize: "var(--font-sm)" }}>
            {subtitle}
          </div>
        </div>

        {children}
      </Stack>
    </section>
  );
}

type SemanticBlockProps = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
};

function SemanticBlock({ title, subtitle, children }: SemanticBlockProps) {
  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: 12,
        background: "rgba(255,255,255,0.02)",
      }}
    >
      <Stack gap={10}>
        <div>
          <div style={{ fontWeight: 800, fontSize: 13 }}>{title}</div>
          {subtitle ? (
            <div className="subtle" style={{ marginTop: 3, fontSize: "var(--font-sm)" }}>
              {subtitle}
            </div>
          ) : null}
        </div>

        {children}
      </Stack>
    </div>
  );
}

export function StatisticalWorkspaceCard(
  props: StatisticalWorkspaceCardProps
) {
  const {
    availableRootArtifacts = [],
    initialRootArtifactRef = null,
    onArtifactProduced,
  } = props;

  const { o6 } = useApi();
  const workspaceClient = React.useMemo(() => createWorkspaceClient(o6), [o6]);

  const [rootArtifactInput, setRootArtifactInput] =
    React.useState<ArtifactRefInput>({
      tool_id: initialRootArtifactRef?.tool_id ?? "",
      fingerprint: initialRootArtifactRef?.fingerprint ?? "",
    });

  const [primaryTargetName, setPrimaryTargetName] = React.useState("t1");
  const [primaryAtrMultiplier, setPrimaryAtrMultiplier] = React.useState(1.0);
  const [secondaryTargetName, setSecondaryTargetName] = React.useState("t2");
  const [secondaryTicks, setSecondaryTicks] = React.useState(4);

  const [scanBaseTarget, setScanBaseTarget] = React.useState("t1");
  const [scanStart, setScanStart] = React.useState(0.5);
  const [scanEnd, setScanEnd] = React.useState(1.5);
  const [scanStep, setScanStep] = React.useState(0.5);

  const [tickSize, setTickSize] = React.useState(0.25);
  const [successTickLevels, setSuccessTickLevels] = React.useState("4, 8");
  const [cleanTickLevels, setCleanTickLevels] = React.useState("2, 4");

  const [cleanQuantBaseTarget, setCleanQuantBaseTarget] =
    React.useState("t1");
  const [cleanAtrThreshold, setCleanAtrThreshold] = React.useState(0.5);

  const [presetName, setPresetName] = React.useState("");
  const [selectedPresetId, setSelectedPresetId] = React.useState("");
  const [importName, setImportName] = React.useState("");
  const [importJson, setImportJson] = React.useState("");
  const [exportJson, setExportJson] = React.useState("");
  const [presetStatus, setPresetStatus] = React.useState("");


  

  const initialBucketizersConfig: BucketizersConfig = {
    volume_bucket: {
      very_low_max: 0,
      low_max: 0,
      medium_max: 0,
      high_max: 0,
    },

    delta_bucket: {
      delta_0_100_max: 0,
      delta_100_300_max: 0,
      delta_300_600_max: 0,
      delta_600_1000_max: 0,
    },

    compression_bucket: {
      ultra_compressed_max: 0,
      compressed_max: 0,
      balanced_max: 0,
      expanded_max: 0,
    },

    atr_bucket: {
      atr_0_0_5_max: 0,
      atr_0_5_1_0_max: 0,
      atr_1_0_1_5_max: 0,
      atr_1_5_2_5_max: 0,
    },

    pre_bo_bucket: {
      pre_neg_max: 0,
      pre_0_2_max: 0,
      pre_2_4_max: 0,
      pre_4_6_max: 0,
    },

    time_bucket: {
      tb_00_04_max: 0,
      tb_04_08_max: 0,
      tb_08_12_max: 0,
      tb_12_16_max: 0,
      tb_16_20_max: 0,
      tb_20_24_max: 0,
    },
  };

const [bucketizersConfig, setBucketizersConfig] =
  React.useState<BucketizersConfig>(initialBucketizersConfig);

const warnings = React.useMemo(() => {
  const errors: {
    domain: string;
    field: string;
    message: string;
    severity: "error";
  }[] = [];

  const isIncreasing = (arr: number[]) =>
    arr.every((v, i) => i === 0 || v > arr[i - 1]);

  const push = (domain: string, field: string, message: string) => {
    errors.push({ domain, field, message, severity: "error" });
  };

  const check = (domain: string, field: string, values: number[]) => {
    if (!isIncreasing(values)) {
      push(domain, field, "Must be strictly increasing");
    }
  };

  check("volume", "volume_bucket.low_max", [
    bucketizersConfig.volume_bucket.very_low_max,
    bucketizersConfig.volume_bucket.low_max,
    bucketizersConfig.volume_bucket.medium_max,
    bucketizersConfig.volume_bucket.high_max,
  ]);

  check("delta", "delta_bucket.delta_0_100_max", [
    bucketizersConfig.delta_bucket.delta_0_100_max,
    bucketizersConfig.delta_bucket.delta_100_300_max,
    bucketizersConfig.delta_bucket.delta_300_600_max,
    bucketizersConfig.delta_bucket.delta_600_1000_max,
  ]);

  return errors;
}, [bucketizersConfig]);

const getError = (field: string) =>
  warnings.find((w) => w.field === field);

  const presets = React.useMemo(
    () => listStatisticalWorkspacePresets(),
    [presetStatus]
  );

  const selectedPreset = React.useMemo(
    () => presets.find((p) => p.id === selectedPresetId) ?? null,
    [presets, selectedPresetId]
  );

  function clearPresetStatusSoon() {
    window.setTimeout(() => setPresetStatus(""), 2500);
  }

  const [state, setState] = React.useState<StatisticalWorkspaceState>({
    loading: false,
    error: null,
    lastRunId: null,
    selectedRootArtifactRef: initialRootArtifactRef,
    artifactRef: null,
    status: "IDLE",
  });


  React.useEffect(() => {
    if (!initialRootArtifactRef) {
      return;
    }

    setRootArtifactInput(initialRootArtifactRef);
    setState((s) => ({
      ...s,
      selectedRootArtifactRef: initialRootArtifactRef,
    }));
  }, [initialRootArtifactRef]);

  function validateArtifactRef(
    value: ArtifactRefInput
  ): ArtifactRefInput | null {
    const tool_id = value.tool_id.trim();
    const fingerprint = value.fingerprint.trim();

    if (!tool_id || !fingerprint) {
      return null;
    }

    return { tool_id, fingerprint };
  }

  function buildConfigObject(): Record<string, unknown> {
    return {
      targets: {
        primary: {
          name: primaryTargetName,
          atr_multiplier: primaryAtrMultiplier,
        },
        secondary: {
          name: secondaryTargetName,
          ticks: secondaryTicks,
        },
      },
      target_scans: {
        success_ATR_scan: {
          base_target: scanBaseTarget,
          x_scan: {
            start: scanStart,
            end: scanEnd,
            step: scanStep,
          },
        },
      },
      tick_scan: {
        tick_size: tickSize,
        success_ticks: {
          levels: parseCsv(successTickLevels).map(Number),
        },
        clean_ticks: {
          levels: parseCsv(cleanTickLevels).map(Number),
        },
      },
      clean_quant: {
        base_target: cleanQuantBaseTarget,
        clean_atr_threshold: cleanAtrThreshold,
      },
      bucketizers: bucketizersConfig,
    };
  }

  function buildPreviewPayload(): StatisticalRunRequest {
    return {
      root_artifact_ref: {
        tool_id: rootArtifactInput.tool_id.trim(),
        fingerprint: rootArtifactInput.fingerprint.trim(),
      },
      config: buildConfigObject(),
    };
  }

  function buildCurrentPayload(): StatisticalRunRequest {
    const root_artifact_ref = validateArtifactRef(rootArtifactInput);

    if (!root_artifact_ref) {
      throw new Error("Root artifact reference is required.");
    }

    if (primaryTargetName.trim() === "") {
      throw new Error("Primary target name is required.");
    }

    if (secondaryTargetName.trim() === "") {
      throw new Error("Secondary target name is required.");
    }

    if (scanBaseTarget.trim() === "") {
      throw new Error("ATR scan base target is required.");
    }

    if (cleanQuantBaseTarget.trim() === "") {
      throw new Error("Clean quant base target is required.");
    }

    if (tickSize <= 0) {
      throw new Error("Tick size must be greater than 0.");
    }

    if (primaryAtrMultiplier <= 0) {
      throw new Error("Primary ATR multiplier must be greater than 0.");
    }

    if (secondaryTicks <= 0) {
      throw new Error("Secondary target ticks must be greater than 0.");
    }

    if (scanStep <= 0) {
      throw new Error("ATR scan step must be greater than 0.");
    }

    if (scanEnd < scanStart) {
      throw new Error("ATR scan end must be greater than or equal to start.");
    }

    return {
      root_artifact_ref,
      config: buildConfigObject(),
    };
  }

  function applyPayloadToForm(payload: StatisticalRunRequest) {
    const rootRef = validateArtifactRef(payload.root_artifact_ref);
    if (rootRef) {
      setRootArtifactInput(rootRef);
      setState((s) => ({
        ...s,
        selectedRootArtifactRef: rootRef,
      }));
    }

    const config = asRecord(payload.config);

    if (config) {
      const targets = asRecord(config.targets);
      const primary = asRecord(targets?.primary);
      const secondary = asRecord(targets?.secondary);

      setPrimaryTargetName(readString(primary?.name, "t1"));
      setPrimaryAtrMultiplier(readNumber(primary?.atr_multiplier, 1.0));
      setSecondaryTargetName(readString(secondary?.name, "t2"));
      setSecondaryTicks(readNumber(secondary?.ticks, 4));

      const targetScans = asRecord(config.target_scans);
      const successAtrScan = asRecord(targetScans?.success_ATR_scan);
      const xScan = asRecord(successAtrScan?.x_scan);

      setScanBaseTarget(readString(successAtrScan?.base_target, "t1"));
      setScanStart(readNumber(xScan?.start, 0.5));
      setScanEnd(readNumber(xScan?.end, 1.5));
      setScanStep(readNumber(xScan?.step, 0.5));

      const tickScan = asRecord(config.tick_scan);
      const successTicks = asRecord(tickScan?.success_ticks);
      const cleanTicks = asRecord(tickScan?.clean_ticks);

      setTickSize(readNumber(tickScan?.tick_size, 0.25));
      setSuccessTickLevels(
        joinCsv(
          (Array.isArray(successTicks?.levels)
            ? successTicks?.levels
            : [4, 8]
          ).map((item) => String(item))
        )
      );
      setCleanTickLevels(
        joinCsv(
          (Array.isArray(cleanTicks?.levels) ? cleanTicks?.levels : [2, 4]).map(
            (item) => String(item)
          )
        )
      );

      const cleanQuant = asRecord(config.clean_quant);
      setCleanQuantBaseTarget(readString(cleanQuant?.base_target, "t1"));
      setCleanAtrThreshold(readNumber(cleanQuant?.clean_atr_threshold, 0.5));

      const bucketizers = asRecord(config.bucketizers);

      if (bucketizers) {
        const volumeBucket = asRecord(bucketizers.volume_bucket);
        const deltaBucket = asRecord(bucketizers.delta_bucket);
        const atrBucket = asRecord(bucketizers.atr_bucket);
        const compressionBucket = asRecord(bucketizers.compression_bucket);
        const preBoBucket = asRecord(bucketizers.pre_bo_bucket);
        const timeBucket = asRecord(bucketizers.time_bucket);

        setBucketizersConfig({
          volume_bucket: {
            very_low_max: readNumber(volumeBucket?.very_low_max, 100),
            low_max: readNumber(volumeBucket?.low_max, 200),
            medium_max: readNumber(volumeBucket?.medium_max, 300),
            high_max: readNumber(volumeBucket?.high_max, 400),
          },
          delta_bucket: {
            delta_0_100_max: readNumber(deltaBucket?.delta_0_100_max, 100),
            delta_100_300_max: readNumber(deltaBucket?.delta_100_300_max, 300),
            delta_300_600_max: readNumber(deltaBucket?.delta_300_600_max, 600),
            delta_600_1000_max: readNumber(deltaBucket?.delta_600_1000_max, 1000),
          },
          atr_bucket: {
            atr_0_0_5_max: readNumber(atrBucket?.atr_0_0_5_max, 0.5),
            atr_0_5_1_0_max: readNumber(atrBucket?.atr_0_5_1_0_max, 1.0),
            atr_1_0_1_5_max: readNumber(atrBucket?.atr_1_0_1_5_max, 1.5),
            atr_1_5_2_5_max: readNumber(atrBucket?.atr_1_5_2_5_max, 2.5),
          },
          compression_bucket: {
            ultra_compressed_max: readNumber(
              compressionBucket?.ultra_compressed_max,
              0.5
            ),
            compressed_max: readNumber(compressionBucket?.compressed_max, 1.0),
            balanced_max: readNumber(compressionBucket?.balanced_max, 1.5),
            expanded_max: readNumber(compressionBucket?.expanded_max, 2.5),
          },
          pre_bo_bucket: {
            pre_neg_max: readNumber(preBoBucket?.pre_neg_max, 0.0),
            pre_0_2_max: readNumber(preBoBucket?.pre_0_2_max, 2.0),
            pre_2_4_max: readNumber(preBoBucket?.pre_2_4_max, 4.0),
            pre_4_6_max: readNumber(preBoBucket?.pre_4_6_max, 6.0),
          },
          time_bucket: {
            tb_00_04_max: readNumber(timeBucket?.tb_00_04_max, 4.0),
            tb_04_08_max: readNumber(timeBucket?.tb_04_08_max, 8.0),
            tb_08_12_max: readNumber(timeBucket?.tb_08_12_max, 12.0),
            tb_12_16_max: readNumber(timeBucket?.tb_12_16_max, 16.0),
            tb_16_20_max: readNumber(timeBucket?.tb_16_20_max, 20.0),
            tb_20_24_max: readNumber(timeBucket?.tb_20_24_max, 24.0),
          },
        });
      }
    }
  }

  React.useEffect(() => {
    try {
      buildCurrentPayload();
    } catch {
      // preview is derived directly from form state
    }
  }, [
    rootArtifactInput.tool_id,
    rootArtifactInput.fingerprint,
    primaryTargetName,
    primaryAtrMultiplier,
    secondaryTargetName,
    secondaryTicks,
    scanBaseTarget,
    scanStart,
    scanEnd,
    scanStep,
    tickSize,
    successTickLevels,
    cleanTickLevels,
    cleanQuantBaseTarget,
    cleanAtrThreshold,
    bucketizersConfig,
  ]);
                                                                 
  async function handleSubmit() {
    try {
      const payload = buildCurrentPayload();

      setState({
        loading: true,
        error: null,
        lastRunId: null,
        selectedRootArtifactRef: payload.root_artifact_ref,
        artifactRef: null,
        status: "PENDING",
      });

      const response = await workspaceClient.postStatisticalRun(payload);

      setState((s) => ({
        ...s,
        loading: true,
        lastRunId: response.run_id,
        artifactRef: response.artifact,
        status: "PENDING",
      }));

      onArtifactProduced?.(response.artifact);
    } catch (error: unknown) {
      let message = "Failed to submit statistical run";

      if (error instanceof Error && error.message) {
        message = error.message;
      } else if (
        typeof error === "object" &&
        error !== null &&
        "message" in error &&
        typeof (error as { message?: unknown }).message === "string"
      ) {
        message = (error as { message: string }).message;
      }

      setState((s) => ({
        ...s,
        loading: false,
        error: message,
        status: "FAILED",
      }));
    }
  }

  function handleSavePreset() {
    try {
      const payload = buildCurrentPayload();
      const saved = saveStatisticalWorkspacePreset(
        presetName || "statistical preset",
        payload
      );
      setSelectedPresetId(saved.id);
      setPresetStatus(`Saved preset: ${saved.name}`);
      setPresetName("");
      clearPresetStatusSoon();
    } catch (error) {
      setPresetStatus((error as Error).message);
    }
  }

  function handleLoadPreset() {
    try {
      if (!selectedPresetId) return;
      const payload = loadStatisticalWorkspacePreset(selectedPresetId);
      applyPayloadToForm(payload);
      setPresetStatus("Preset loaded.");
      clearPresetStatusSoon();
    } catch (error) {
      setPresetStatus((error as Error).message);
    }
  }
  function handleDeletePreset() {
    try {
      if (!selectedPresetId) return;
      deleteStatisticalWorkspacePreset(selectedPresetId);
      setSelectedPresetId("");
      setExportJson("");
      setPresetStatus("Preset deleted.");
      clearPresetStatusSoon();
    } catch (error) {
      setPresetStatus((error as Error).message);
    }
  }

  function handleExportPreset() {
    try {
      if (!selectedPresetId) return;
      const json = exportStatisticalWorkspacePresetJson(selectedPresetId);
      setExportJson(json);
      setPresetStatus("Preset exported.");
      clearPresetStatusSoon();
    } catch (error) {
      setPresetStatus((error as Error).message);
    }
  }

  function handleOpenResults() {
    if (!state.artifactRef) return;

    const { tool_id, fingerprint } = state.artifactRef;

    const url = routes.workspaceStatisticalResults(tool_id, fingerprint);
    window.open(url, "_blank", "noopener,noreferrer");
  }

  function handleImportPreset() {
    try {
      const saved = importStatisticalWorkspacePresetJson(
        importName || "imported statistical preset",
        importJson
      );
      setSelectedPresetId(saved.id);
      setImportName("");
      setImportJson("");
      setPresetStatus(`Imported preset: ${saved.name}`);
      clearPresetStatusSoon();
    } catch (error) {
      setPresetStatus((error as Error).message);
    }
  }

  React.useEffect(() => {
    if (!state.lastRunId) return;

    let isActive = true;

    const interval = window.setInterval(async () => {
      try {
        const run = await o6.getRun(state.lastRunId as string);

        if (!isActive) return;

        const status = run.status;

        if (status === "PENDING" || status === "RUNNING") {
          setState((s) => ({
            ...s,
            status,
            loading: true,
          }));
          return;
        }

        if (status === "SUCCEEDED") {
          setState((s) => ({
            ...s,
            status: "SUCCEEDED",
            loading: false,
          }));
          window.clearInterval(interval);
          return;
        }

        if (status === "FAILED") {
          setState((s) => ({
            ...s,
            status: "FAILED",
            loading: false,
          }));
          window.clearInterval(interval);
        }
      } catch {
        if (!isActive) return;

        setState((s) => ({
          ...s,
          status: "NOT_FOUND",
          loading: false,
        }));

        window.clearInterval(interval);
      }
    }, 2500);

    return () => {
      isActive = false;
      window.clearInterval(interval);
    };
  }, [state.lastRunId, o6]);

  const isValid = validateArtifactRef(rootArtifactInput) !== null;

  const datasetColumnSuggestions = React.useMemo(
    () => [
      "breakout_id",
      "parent_balance_id",
      "instrument",
      "symbol",
      "session_id",
      "timeframe",
      "breakout_time",
      "breakout_bar_index",
      "confirmation_time",
      "confirmation_bar_index",
      "computation_timestamp",
      "version",
      "direction",
      "breakout_type",
      "confirmation_status",
      "breakout_price",
      "confirmation_price",
      "boundary_price",
      "boundary_type",
      "balance_high",
      "balance_low",
      "balance_midpoint",
      "balance_range_size",
      "balance_vpoc",
      "balance_hvn",
      "balance_lvn",
      "balance_equilibrium_score",
      "initial_volume",
      "initial_delta",
      "atr_before",
      "atr_after",
      "follow_through",
      "pre_breakout_signal",
      "is_failed",
      "schema_version",
      "side",
      "range_atr_ratio",
      "balance_pressure",
      "breakout_location_ratio",
      "abs_initial_delta",
      "initial_volume_feature",
      "volume_atr_ratio",
      "volume_range_ratio",
      "ml_distance_atr",
      "max_excursion",
      "breakout_efficiency",
      "pre_total_score",
      "hour",
      "session_calc",
      "weekday",
      "day_of_month",
      "week_of_month",
      "year",
      "breakout_outcome",
    ],
    []
  );

  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: 8,
    borderRadius: 8,
  };



  return (
    <Card>
      <CardHeader>
        <CardTitle>Statistical Stage</CardTitle>
      </CardHeader>

      <CardContent>
        <Stack gap={20}>
          <Stack gap={8}>
            <div className="subtle">
              Guided configuration for the Statistical stage. The final payload
              still matches the public contract exactly.
            </div>
          </Stack>

          <datalist id="statistical-dataset-columns">
            {datasetColumnSuggestions.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 1fr) 320px",
              gap: 16,
              alignItems: "stretch",
            }}
          >
            <SemanticSection
              title="Root Artifact"
              subtitle="Select the Root output used to build the statistical dataset."
              badge="INPUT"
            >
              <ArtifactSelector
                available={availableRootArtifacts}
                selected={state.selectedRootArtifactRef}
                onSelect={(ref) => {
                  setRootArtifactInput(ref);
                  setState((s) => ({
                    ...s,
                    selectedRootArtifactRef: ref,
                  }));
                }}
                onManualChange={(ref) => {
                  setRootArtifactInput(ref ?? { tool_id: "", fingerprint: "" });
                  setState((s) => ({
                    ...s,
                    selectedRootArtifactRef: ref,
                  }));
                }}
              />
            </SemanticSection>

            <SemanticSection
              title="Saved Config"
              subtitle="Save / restore Statistical workspace state."
              badge="DEBUG"
            >
              <Stack gap={8}>
                {presetStatus ? <div className="pill">{presetStatus}</div> : null}

                <FormField
                  label="Preset name"
                  hint="Save the current Statistical form values."
                >
                  <Stack direction="row" gap={8}>
                    <input
                      type="text"
                      value={presetName}
                      onChange={(e) => setPresetName(e.target.value)}
                      placeholder="Preset name"
                      style={{ minWidth: 0 }}
                    />
                    <Button onClick={handleSavePreset} variant="secondary" disabled={!isValid}>
                      Save
                    </Button>
                  </Stack>
                </FormField>

                <FormField
                  label="Saved preset"
                  hint="Restore, delete or export a saved configuration."
                >
                  <Stack gap={8}>
                    <select
                      value={selectedPresetId}
                      onChange={(e) => setSelectedPresetId(e.target.value)}
                    >
                      <option value="">Select preset</option>
                      {presets.map((preset) => (
                        <option key={preset.id} value={preset.id}>
                          {preset.name}
                        </option>
                      ))}
                    </select>

                    <Grid columns="1fr 1fr 1fr" gap={8}>
                      <Button onClick={handleLoadPreset} variant="secondary" disabled={!selectedPresetId}>
                        Load
                      </Button>
                      <Button onClick={handleDeletePreset} variant="danger" disabled={!selectedPresetId}>
                        Delete
                      </Button>
                      <Button onClick={handleExportPreset} variant="secondary" disabled={!selectedPresetId}>
                        Export
                      </Button>
                    </Grid>
                  </Stack>
                </FormField>

                {selectedPreset ? (
                  <div className="pill">Selected: {selectedPreset.name}</div>
                ) : null}

                <Collapsible
                  title="Import / export JSON"
                  subtitle="Backup or manual restore"
                  defaultOpen={false}
                  compact={true}
                  meta="Advanced"
                >
                  <Stack gap={8}>
                    <textarea
                      value={exportJson}
                      readOnly
                      rows={3}
                      placeholder="Exported preset JSON"
                      style={{ width: "100%", fontFamily: "monospace", fontSize: 11 }}
                    />

                    <input
                      type="text"
                      value={importName}
                      onChange={(e) => setImportName(e.target.value)}
                      placeholder="Imported preset name"
                    />

                    <textarea
                      value={importJson}
                      onChange={(e) => setImportJson(e.target.value)}
                      rows={3}
                      placeholder="Paste preset JSON here"
                      style={{ width: "100%", fontFamily: "monospace", fontSize: 11 }}
                    />

                    <Button
                      onClick={handleImportPreset}
                      variant="secondary"
                      disabled={!importJson.trim()}
                    >
                      Import
                    </Button>
                  </Stack>
                </Collapsible>
              </Stack>
            </SemanticSection>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ fontWeight: 800, fontSize: 16 }}>
              Statistical Configuration Layer
            </div>

            <div className="subtle">
              Refines a Root artifact into statistical features and derived evaluation buckets.
            </div>
          </div>

          <Collapsible
            title="Target System"
            subtitle="Defines target columns, thresholds, scans and clean movement labels"
            defaultOpen={true}
            compact={true}
            meta="CORE"
          >
            <Stack gap={18}>
              <div>
                <div style={{ fontWeight: 800 }}>Output target names</div>
                <div className="subtle" style={{ fontSize: "var(--font-sm)", marginTop: 4 }}>
                  Names of the generated base target columns. These names are referenced by scans and clean logic.
                </div>
              </div>

              <Grid columns="1fr 1fr" gap={12}>
                <FormField label="Primary target column" hint="Column name for the ATR-based primary target." example="Example: t1.">
                  <input value={primaryTargetName} onChange={(e) => setPrimaryTargetName(e.target.value)} placeholder="e.g. t1" />
                </FormField>

                <FormField label="Secondary target column" hint="Column name for the tick-based secondary target." example="Example: t2.">
                  <input value={secondaryTargetName} onChange={(e) => setSecondaryTargetName(e.target.value)} placeholder="e.g. t2" />
                </FormField>
              </Grid>

              <div>
                <div style={{ fontWeight: 800 }}>Base target thresholds</div>
                <div className="subtle" style={{ fontSize: "var(--font-sm)", marginTop: 4 }}>
                  Core success thresholds used to generate the base target columns.
                </div>
              </div>

              <Grid columns="1fr 1fr 1fr" gap={12}>
                <FormField label="Primary ATR target" hint="Success requires max excursion to reach this ATR multiple." example="Example: 1.0 = 1x ATR.">
                  <input type="number" step="0.1" value={primaryAtrMultiplier} onChange={(e) => setPrimaryAtrMultiplier(Number(e.target.value))} />
                </FormField>

                <FormField label="Secondary tick target" hint="Success requires max excursion to reach this many ticks." example="Example: 4 ticks.">
                  <input type="number" value={secondaryTicks} onChange={(e) => setSecondaryTicks(Number(e.target.value))} />
                </FormField>

                <FormField label="Tick size" hint="Price value of one tick. Used by all tick-based targets." example="Example: 0.25.">
                  <input type="number" step="0.01" value={tickSize} onChange={(e) => setTickSize(Number(e.target.value))} placeholder="e.g. 0.25" />
                </FormField>
              </Grid>

              <div>
                <div style={{ fontWeight: 800 }}>ATR target family</div>
                <div className="subtle" style={{ fontSize: "var(--font-sm)", marginTop: 4 }}>
                  Generates additional ATR target columns from a start/end/step range.
                </div>
              </div>

              <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                <FormField label="Base target" hint="Target family used as the scan base." example="Example: t1.">
                  <input value={scanBaseTarget} onChange={(e) => setScanBaseTarget(e.target.value)} placeholder="e.g. t1" />
                </FormField>

                <FormField label="Scan start" hint="First ATR multiple generated by the scan." example="Unit: ATR multiple.">
                  <input type="number" step="0.1" value={scanStart} onChange={(e) => setScanStart(Number(e.target.value))} />
                </FormField>

                <FormField label="Scan end" hint="Last ATR multiple generated by the scan." example="Unit: ATR multiple.">
                  <input type="number" step="0.1" value={scanEnd} onChange={(e) => setScanEnd(Number(e.target.value))} />
                </FormField>

                <FormField label="Scan step" hint="Increment between generated ATR target columns." example="Unit: ATR multiple.">
                  <input type="number" step="0.1" value={scanStep} onChange={(e) => setScanStep(Number(e.target.value))} />
                </FormField>
              </Grid>

              <div>
                <div style={{ fontWeight: 800 }}>Tick target family</div>
                <div className="subtle" style={{ fontSize: "var(--font-sm)", marginTop: 4 }}>
                  Generates additional tick-based success and clean target columns.
                </div>
              </div>

              <Grid columns="1fr 1fr" gap={12}>
                <FormField label="Success tick levels" hint="Comma-separated tick targets used to generate success target columns." example="Example: 4, 8.">
                  <input value={successTickLevels} onChange={(e) => setSuccessTickLevels(e.target.value)} placeholder="e.g. 4, 8" />
                </FormField>

                <FormField
                  label="Clean tick levels"
                  hint="Comma-separated tick targets using separate clean-target logic."
                  example="Example: 2, 4."
                  tone="warning"
                  note="Clean tick targets are not the same as Clean Quant."
                >
                  <input value={cleanTickLevels} onChange={(e) => setCleanTickLevels(e.target.value)} placeholder="e.g. 2, 4" />
                </FormField>
              </Grid>

              <div>
                <div style={{ fontWeight: 800 }}>Clean Quant logic</div>
                <div className="subtle" style={{ fontSize: "var(--font-sm)", marginTop: 4 }}>
                  Labels movement quality using retracement depth relative to max excursion.
                </div>
              </div>

              <Grid columns="1fr 1fr" gap={12}>
                <FormField
                  label="Clean Quant base target"
                  hint="Target that must be true before Clean Quant can pass."
                  example="Example: t1."
                >
                  <input
                    value={cleanQuantBaseTarget}
                    onChange={(e) => setCleanQuantBaseTarget(e.target.value)}
                    placeholder="e.g. t1"
                  />
                </FormField>

                <FormField
                  label="Clean retracement threshold"
                  hint="Requires retracement_depth / max_excursion to stay below this ratio."
                  example="Example: 0.5 allows up to 50% retracement."
                  tone="warning"
                  note="Clean Quant uses a ratio; Clean tick targets use separate ATR-threshold logic."
                >
                  <input
                    type="number"
                    step="0.1"
                    value={cleanAtrThreshold}
                    onChange={(e) => setCleanAtrThreshold(Number(e.target.value))}
                  />
                </FormField>
              </Grid>
            </Stack>
          </Collapsible>

          
          <Stack gap={16}>
          <Collapsible
            title="Bucketizers"
            subtitle="Analytical grouping buckets. These classify rows but do not create targets."
            defaultOpen={false}
            compact={true}
            meta="Classification"
          >
            <div
              style={{
                border: "1px solid rgba(120,120,255,0.25)",
                borderRadius: 12,
                padding: 12,
                background: "rgba(120,120,255,0.04)",
              }}
            >
              <Stack gap={16}>
                <div className="subtle">
                  Feature engineering thresholds grouped by domain. These do not affect detection logic.
                </div>

                {/* ================= FLOW ================= */}
                <Collapsible
                  title="Flow"
                  subtitle="Volume and delta classification"
                  defaultOpen={false}
                  compact={true}
                >
                  <Stack gap={12}>

                    <div style={{ fontWeight: 800 }}>Volume</div>

                    <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                      {[
                        "very_low_max",
                        "low_max",
                        "medium_max",
                        "high_max",
                      ].map((key) => {
                        const field = `volume_bucket.${key}`;
                        const error = getError(field);

                        return (
                          <FormField key={key} label={getBucketLabel(key)}>
                            <input
                              type="number"
                              value={(bucketizersConfig.volume_bucket as any)[key]}
                              onChange={(e) =>
                                setBucketizersConfig((prev) => ({
                                  ...prev,
                                  volume_bucket: {
                                    ...prev.volume_bucket,
                                    [key]: Number(e.target.value),
                                  },
                                }))
                              }
                              style={{
                                border: error ? "1px solid red" : undefined,
                              }}
                            />

                            {error ? (
                              <div style={{ color: "red", fontSize: 12 }}>
                                {error.message}
                              </div>
                            ) : null}
                          </FormField>
                        );
                      })}
                    </Grid>

                    <div style={{ fontWeight: 800 }}>Delta</div>

                    <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                      {[
                        "delta_0_100_max",
                        "delta_100_300_max",
                        "delta_300_600_max",
                        "delta_600_1000_max",
                      ].map((key) => {
                        const field = `delta_bucket.${key}`;
                        const error = getError(field);

                        return (
                          <FormField key={key} label={getBucketLabel(key)}>
                            <input
                              type="number"
                              value={(bucketizersConfig.delta_bucket as any)[key]}
                              onChange={(e) =>
                                setBucketizersConfig((prev) => ({
                                  ...prev,
                                  delta_bucket: {
                                    ...prev.delta_bucket,
                                    [key]: Number(e.target.value),
                                  },
                                }))
                              }
                              style={{
                                border: error ? "1px solid red" : undefined,
                              }}
                            />

                            {error ? (
                              <div style={{ color: "red", fontSize: 12 }}>
                                {error.message}
                              </div>
                            ) : null}
                          </FormField>
                        );
                      })}
                    </Grid>

                  </Stack>
                </Collapsible>

                {/* ================= MARKET REGIME ================= */}
                <Collapsible
                  title="Market Regime"
                  subtitle="Volatility and compression classification layer"
                  defaultOpen={false}
                  compact={true}
                >
                  <Stack gap={12}>

                    <div style={{ fontWeight: 800 }}>Compression</div>

                    <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                      {[
                        "ultra_compressed_max",
                        "compressed_max",
                        "balanced_max",
                        "expanded_max",
                      ].map((key) => {
                        const field = `compression_bucket.${key}`;
                        const error = getError(field);

                        return (
                          <FormField key={key} label={getBucketLabel(key)}>
                            <input
                              type="number"
                              step="0.01"
                              value={(bucketizersConfig.compression_bucket as any)[key]}
                              onChange={(e) =>
                                setBucketizersConfig((prev) => ({
                                  ...prev,
                                  compression_bucket: {
                                    ...prev.compression_bucket,
                                    [key]: Number(e.target.value),
                                  },
                                }))
                              }
                              style={{
                                border: error ? "1px solid red" : undefined,
                              }}
                            />

                            {error ? (
                              <div style={{ color: "red", fontSize: 12 }}>
                                {error.message}
                              </div>
                            ) : null}
                          </FormField>
                        );
                      })}
                    </Grid>

                    <div style={{ fontWeight: 800 }}>ATR</div>

                    <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                      {[
                        "atr_0_0_5_max",
                        "atr_0_5_1_0_max",
                        "atr_1_0_1_5_max",
                        "atr_1_5_2_5_max",
                      ].map((key) => {
                        const field = `atr_bucket.${key}`;
                        const error = getError(field);

                        return (
                          <FormField key={key} label={getBucketLabel(key)}>
                            <input
                              type="number"
                              step="0.01"
                              value={(bucketizersConfig.atr_bucket as any)[key]}
                              onChange={(e) =>
                                setBucketizersConfig((prev) => ({
                                  ...prev,
                                  atr_bucket: {
                                    ...prev.atr_bucket,
                                    [key]: Number(e.target.value),
                                  },
                                }))
                              }
                              style={{
                                border: error ? "1px solid red" : undefined,
                              }}
                            />

                            {error ? (
                              <div style={{ color: "red", fontSize: 12 }}>
                                {error.message}
                              </div>
                            ) : null}
                          </FormField>
                        );
                      })}
                    </Grid>

                  </Stack>
                </Collapsible>

                {/* ================= SETUP ================= */}
                <Collapsible
                  title="Setup (Pre-breakout)"
                  subtitle="Early signal classification before structural breakout"
                  defaultOpen={false}
                  compact={true}
                >
                  <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                    {[
                      "pre_neg_max",
                      "pre_0_2_max",
                      "pre_2_4_max",
                      "pre_4_6_max",
                    ].map((key) => {
                      const field = `pre_bo_bucket.${key}`;
                      const error = getError(field);

                      return (
                        <FormField key={key} label={getBucketLabel(key)}>
                          <input
                            type="number"
                            step="0.01"
                            value={(bucketizersConfig.pre_bo_bucket as any)[key]}
                            onChange={(e) =>
                              setBucketizersConfig((prev) => ({
                                ...prev,
                                pre_bo_bucket: {
                                  ...prev.pre_bo_bucket,
                                  [key]: Number(e.target.value),
                                },
                              }))
                            }
                            style={{
                              border: error ? "1px solid red" : undefined,
                            }}
                          />

                          {error ? (
                            <div style={{ color: "red", fontSize: 12 }}>
                              {error.message}
                            </div>
                          ) : null}
                        </FormField>
                      );
                    })}
                  </Grid>
                </Collapsible>

                {/* ================= TEMPORAL ================= */}
                <Collapsible
                  title="Temporal"
                  subtitle="Session-based time segmentation"
                  defaultOpen={false}
                  compact={true}
                >
                  <Grid columns="1fr 1fr 1fr 1fr 1fr 1fr" gap={12}>
                    {[
                      "tb_00_04_max",
                      "tb_04_08_max",
                      "tb_08_12_max",
                      "tb_12_16_max",
                      "tb_16_20_max",
                      "tb_20_24_max",
                    ].map((key) => {
                      const field = `time_bucket.${key}`;
                      const error = getError(field);

                      return (
                        <FormField key={key} label={getBucketLabel(key)}>
                          <input
                            type="number"
                            step="0.01"
                            value={(bucketizersConfig.time_bucket as any)[key]}
                            onChange={(e) =>
                              setBucketizersConfig((prev) => ({
                                ...prev,
                                time_bucket: {
                                  ...prev.time_bucket,
                                  [key]: Number(e.target.value),
                                },
                              }))
                            }
                            style={{
                              border: error ? "1px solid red" : undefined,
                            }}
                          />

                          {error ? (
                            <div style={{ color: "red", fontSize: 12 }}>
                              {error.message}
                            </div>
                          ) : null}
                        </FormField>
                      );
                    })}
                  </Grid>
                </Collapsible>

              </Stack>
            </div>
          </Collapsible>

              {/* ================= PAYLOAD ================= */}
              <Collapsible
                title="Payload preview"
                subtitle="Exact payload sent to the runtime. This must remain unchanged by UX copy"
                defaultOpen={false}
                compact={true}
              >
                <Stack gap={12}>
                  <textarea
                    value={JSON.stringify(buildPreviewPayload(), null, 2)}
                    readOnly
                    rows={20}
                    style={{ width: "100%", fontFamily: "monospace" }}
                  />
                </Stack>
              </Collapsible>

            </Stack>
          {state.selectedRootArtifactRef ? (
            <div style={{ border: "1px solid #ccc", padding: 12, borderRadius: 8 }}>
              <strong>Lineage</strong>
              <div>Derived from Root Artifact</div>
            </div>
          ) : null}

          <div>
            <StepStatusBanner
              status={state.status}
              loading={state.loading}
              error={state.error}
              lastRunId={state.lastRunId}
            />
          </div>

          <div>
            <div style={{ marginBottom: 8 }}>
              <strong>Selected root artifact</strong>
            </div>
            <ArtifactRefBadge
              artifactRef={state.selectedRootArtifactRef}
              origin="root"
              copyable
            />
          </div>

          <div>
            <div style={{ marginBottom: 8 }}>
              <strong>Produced statistical artifact</strong>
            </div>
            <ArtifactRefBadge
              artifactRef={state.artifactRef}
              origin="statistical"
              copyable
            />
          </div>
        </Stack>
      </CardContent>

      <CardFooter>
        <div
          style={{
            display: "flex",
            gap: 12,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          <Button onClick={handleSubmit} disabled={!isValid || state.loading}>
            {state.loading ? "Running..." : "Run Statistical Stage"}
          </Button>

          <Button
            variant="secondary"
            onClick={handleOpenResults}
            disabled={!state.artifactRef}
          >
            View Results
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}