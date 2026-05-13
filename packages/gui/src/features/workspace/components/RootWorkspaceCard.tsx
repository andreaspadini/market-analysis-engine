import React from "react";
import { useApi } from "../../../api/ApiProvider";
import { routes } from "../../../app/routes";
import { createWorkspaceClient } from "../api/workspaceClient";
import type { RootWorkspaceState } from "../model/rootWorkspaceState";
import type {
  ArtifactRefInput,
  RootRunRequest,
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
import { StepStatusBanner } from "./StepStatusBanner";
import { ArtifactRefBadge } from "./ArtifactRefBadge";
import {
  listRootWorkspacePresets,
  saveRootWorkspacePreset,
  loadRootWorkspacePreset,
  deleteRootWorkspacePreset,
  exportRootWorkspacePresetJson,
  importRootWorkspacePresetJson,
} from "../model/rootWorkspacePresets";

type RootWorkspaceCardProps = {
  onArtifactProduced?: (artifactRef: ArtifactRefInput | null) => void;
};

type SemanticSectionProps = {
  title: string;
  subtitle: string;
  badge: "CORE" | "SECONDARY" | "ADVANCED" | "CLASSIFICATION" | "DEBUG";
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

export function RootWorkspaceCard({ onArtifactProduced }: RootWorkspaceCardProps) {
    const { o6 } = useApi();

    const workspaceClient = React.useMemo(
      () => createWorkspaceClient(o6),
      [o6]
    );


  const [instrument, setInstrument] = React.useState("MNQ");
  const [timeframe, setTimeframe] = React.useState("1m");
  const [startDate, setStartDate] = React.useState("2025-11-01");
  const [endDate, setEndDate] = React.useState("2025-12-31");

  const [rotationMethod, setRotationMethod] = React.useState("mid_range");
  const [mergeSameDirection, setMergeSameDirection] = React.useState(true);

  const [minRotationBars, setMinRotationBars] = React.useState(0);

  const [minRotationAmplitude, setMinRotationAmplitude] = React.useState(0.25);
  const [minRotationAmplitudeMicro, setMinRotationAmplitudeMicro] = React.useState(0.5);
  const [minRotationAmplitudeStandard, setMinRotationAmplitudeStandard] = React.useState(1);
  const [minRotationAmplitudeStructural, setMinRotationAmplitudeStructural] = React.useState(5);

  const [whipsawBars, setWhipsawBars] = React.useState(1);

  const [breakoutMode, setBreakoutMode] = React.useState("strict");
  const [confirmationEnabled, setConfirmationEnabled] = React.useState(true);


  const [balanceMinRotations, setBalanceMinRotations] = React.useState(2);
  const [balanceMaxGapBars, setBalanceMaxGapBars] = React.useState(10);
  const [balanceMinBars, setBalanceMinBars] = React.useState(5);
  const [balanceMinWidth, setBalanceMinWidth] = React.useState(0.3);
  const [balanceMaxWidth, setBalanceMaxWidth] = React.useState(6.0);

  const [balanceVpMinTotalVolume, setBalanceVpMinTotalVolume] = React.useState(0);
  const [balanceVpBinSize, setBalanceVpBinSize] = React.useState(0.05);
  const [balanceVpHvnThresholdFactor, setBalanceVpHvnThresholdFactor] = React.useState(1.2);
  const [balanceVpLvnThresholdFactor, setBalanceVpLvnThresholdFactor] = React.useState(0.8);
  const [balanceVpWindowAroundPoc, setBalanceVpWindowAroundPoc] = React.useState(0.25);
  const [balanceVpWindowAroundMid, setBalanceVpWindowAroundMid] = React.useState(0.25);

  const [balanceClsCompressedWidthFactor, setBalanceClsCompressedWidthFactor] =
    React.useState(0.25);
  const [balanceClsWideWidthFactor, setBalanceClsWideWidthFactor] =
    React.useState(1.75);
  const [balanceClsAsymmetryThreshold, setBalanceClsAsymmetryThreshold] =
    React.useState(0.25);
  const [balanceClsCenterVolumeThreshold, setBalanceClsCenterVolumeThreshold] =
    React.useState(0.35);
  const [balanceClsEdgeVolumeThreshold, setBalanceClsEdgeVolumeThreshold] =
    React.useState(0.2);
  const [balanceClsHvnDensityThreshold, setBalanceClsHvnDensityThreshold] =
    React.useState(0.2);
  const [balanceClsLvnDensityThreshold, setBalanceClsLvnDensityThreshold] =
    React.useState(0.1);

  const [postBalanceBars, setPostBalanceBars] = React.useState(5);
  const [breakoutBodyMargin, setBreakoutBodyMargin] = React.useState(0.0);
  const [confirmationMaxBars, setConfirmationMaxBars] = React.useState(5);
  const [confirmationClosesRequired, setConfirmationClosesRequired] =
    React.useState(1);
  const [confirmationDeltaEnabled, setConfirmationDeltaEnabled] =
    React.useState(false);
  const [confirmationDeltaMinAbs, setConfirmationDeltaMinAbs] =
    React.useState(0.0);

  const [sessionLevelsVersion, setSessionLevelsVersion] = React.useState("1.0");
  const [asiaOpen, setAsiaOpen] = React.useState("00:00");
  const [asiaClose, setAsiaClose] = React.useState("08:00");
  const [asiaTimezone, setAsiaTimezone] = React.useState("UTC");
  const [europeOpen, setEuropeOpen] = React.useState("08:00");
  const [europeClose, setEuropeClose] = React.useState("16:00");
  const [europeTimezone, setEuropeTimezone] = React.useState("UTC");
  const [usaOpen, setUsaOpen] = React.useState("16:00");
  const [usaClose, setUsaClose] = React.useState("23:00");
  const [usaTimezone, setUsaTimezone] = React.useState("UTC");

  const [sessionVpBinSize, setSessionVpBinSize] = React.useState(1.0);
  const [sessionVpValueAreaPct, setSessionVpValueAreaPct] = React.useState(0.7);
  const [sessionVwapEnabled, setSessionVwapEnabled] = React.useState(true);

  const [presetName, setPresetName] = React.useState("");
  const [selectedPresetId, setSelectedPresetId] = React.useState("");
  const [importName, setImportName] = React.useState("");
  const [importJson, setImportJson] = React.useState("");
  const [exportJson, setExportJson] = React.useState("");
  const [presetStatus, setPresetStatus] = React.useState("");
  const [rawJson, setRawJson] = React.useState("");
  const [rawError, setRawError] = React.useState<string | null>(null);
    const [preBreakoutEnabled, setPreBreakoutEnabled] = React.useState(true);
  const [preBreakoutVolatilityWindow, setPreBreakoutVolatilityWindow] =
    React.useState(20);
  const [preBreakoutMinVolatilityIncrease, setPreBreakoutMinVolatilityIncrease] =
    React.useState(1.0);
  const [preBreakoutMaxLvnDistance, setPreBreakoutMaxLvnDistance] =
    React.useState(0.25);
  const [preBreakoutMinDeltaBias, setPreBreakoutMinDeltaBias] =
    React.useState(0.15);
  const [preBreakoutBoundaryVolumeFactor, setPreBreakoutBoundaryVolumeFactor] =
    React.useState(0.5);
  const [preBreakoutMinScore, setPreBreakoutMinScore] = React.useState(0.55);
  const [preBreakoutMaxLeadMinutes, setPreBreakoutMaxLeadMinutes] =
    React.useState(30);

  const [preBreakoutWeightCompression, setPreBreakoutWeightCompression] =
    React.useState(0.3);
  const [preBreakoutWeightLvnProximity, setPreBreakoutWeightLvnProximity] =
    React.useState(0.3);
  const [preBreakoutWeightVolatility, setPreBreakoutWeightVolatility] =
    React.useState(0.2);
  const [preBreakoutWeightDeltaBias, setPreBreakoutWeightDeltaBias] =
    React.useState(0.2);

  const [preBreakoutTriggerType, setPreBreakoutTriggerType] =
    React.useState("close");
  const [preBreakoutTriggerMinConsecutive, setPreBreakoutTriggerMinConsecutive] =
    React.useState(1);
  const [preBreakoutTriggerMinPenetration, setPreBreakoutTriggerMinPenetration] =
    React.useState(0.0);

  const [preBreakoutFilterMinVolumeRatio, setPreBreakoutFilterMinVolumeRatio] =
    React.useState(0.5);
  const [preBreakoutFilterMinVolatilityRatio, setPreBreakoutFilterMinVolatilityRatio] =
    React.useState(0.5);
  const [earlyDetectionEnabled, setEarlyDetectionEnabled] = React.useState(false);
  const [earlyDetectionLowerTimeframe, setEarlyDetectionLowerTimeframe] = React.useState("1m");
  const [earlyDetectionReferenceTimeframe, setEarlyDetectionReferenceTimeframe] = React.useState("5m");
  const [earlyDetectionMaxLeadMinutes, setEarlyDetectionMaxLeadMinutes] =
    React.useState(10);
  const [earlyDetectionTriggerType, setEarlyDetectionTriggerType] =
    React.useState("close");
  const [
    earlyDetectionTriggerMinConsecutive,
    setEarlyDetectionTriggerMinConsecutive,
  ] = React.useState(1);
  const [
    earlyDetectionTriggerMinPenetration,
    setEarlyDetectionTriggerMinPenetration,
  ] = React.useState(0);

  const [strengthMomentumWeight, setStrengthMomentumWeight] =
    React.useState(1.0);
  const [strengthDeltaWeight, setStrengthDeltaWeight] = React.useState(1.0);
  const [strengthVolumeSpikeWeight, setStrengthVolumeSpikeWeight] =
    React.useState(1.0);
  const [strengthVolatilityWeight, setStrengthVolatilityWeight] =
    React.useState(1.0);
  const [strengthDistanceFromVpocWeight, setStrengthDistanceFromVpocWeight] =
    React.useState(0.5);
  const [strengthHvnLvnBreakWeight, setStrengthHvnLvnBreakWeight] =
    React.useState(0.5);

  const [strengthNormalizationEnabled, setStrengthNormalizationEnabled] =
    React.useState(true);
  const [strengthNormalizationMethod, setStrengthNormalizationMethod] =
    React.useState("minmax");
  const [strengthNormalizationMinRaw, setStrengthNormalizationMinRaw] =
    React.useState(0.0);
  const [strengthNormalizationMaxRaw, setStrengthNormalizationMaxRaw] =
    React.useState(6.0);
  const [strengthNormalizationSigmoidK, setStrengthNormalizationSigmoidK] =
    React.useState(1.0);

  const [atrEnabled, setAtrEnabled] = React.useState(true);
  const [atrPeriod, setAtrPeriod] = React.useState(14);
  const [atrUseForStrength, setAtrUseForStrength] = React.useState(true);
  const [atrNormalizationFactor, setAtrNormalizationFactor] =
    React.useState(1.0);

  const [volatilityFilterEnabled, setVolatilityFilterEnabled] =
    React.useState(false);
  const [volatilityFilterMinCompressionRatio, setVolatilityFilterMinCompressionRatio] =
    React.useState(0.4);
  const [volatilityFilterMaxCompressionRatio, setVolatilityFilterMaxCompressionRatio] =
    React.useState(1.2);
  const [volatilityFilterMinStabilityScore, setVolatilityFilterMinStabilityScore] =
    React.useState(0.3);
  const [volatilityFilterSoftPenalty, setVolatilityFilterSoftPenalty] =
    React.useState(0.35);

  const [followThroughObservationBars, setFollowThroughObservationBars] =
    React.useState(15);

  const [followThroughRetestWindow, setFollowThroughRetestWindow] =
    React.useState(10);
  const [followThroughBoundaryHoldBars, setFollowThroughBoundaryHoldBars] =
    React.useState(1);

  const [rotationsFilterMinRotations, setRotationsFilterMinRotations] =
    React.useState(0);
  const [rotationsFilterMinDirectionalBias, setRotationsFilterMinDirectionalBias] =
    React.useState(0.0);
  const [
    breakoutRequireStructuralRotation,
    setBreakoutRequireStructuralRotation,
  ] = React.useState(false);

  const [balanceClsEquilibriumScore, setBalanceClsEquilibriumScore] =
    React.useState("");

  const presets = React.useMemo(() => listRootWorkspacePresets(), [presetStatus]);

  const selectedPreset = React.useMemo(
    () => presets.find((p) => p.id === selectedPresetId) ?? null,
    [presets, selectedPresetId]
  );

  function normalizeDatasetDate(value: string): string {
    return value.trim();
  }

  function handleViewResults() {
    if (!state.artifactRef) return;

    const url = routes.workspaceRootResults(
      state.artifactRef.tool_id,
      state.artifactRef.fingerprint
    );

    window.open(url, "_blank", "noopener,noreferrer");
  }

  function clearPresetStatusSoon() {
    window.setTimeout(() => setPresetStatus(""), 2500);
  }

  const [state, setState] = React.useState<RootWorkspaceState>({
    loading: false,
    error: null,
    lastRunId: null,
    artifactRef: null,
    status: "IDLE",
  });

  const isValid =
    instrument.trim() !== "" &&
    timeframe.trim() !== "" &&
    startDate.trim() !== "" &&
    endDate.trim() !== "" &&
    new Date(endDate) >= new Date(startDate);
  
  function buildConfigObject(): Record<string, unknown> {
    return {
      rotations: {
        merge_same_direction: mergeSameDirection,
        whipsaw_bars: whipsawBars,
        min_rotation_bars: Math.max(1, minRotationBars),
        min_rotation_amplitude: minRotationAmplitude,
        min_rotation_amplitude_micro: minRotationAmplitudeMicro,
        min_rotation_amplitude_standard: minRotationAmplitudeStandard,
        min_rotation_amplitude_structural: minRotationAmplitudeStructural,
      },
      balance: {
        min_rotations: balanceMinRotations,
        max_gap_bars: balanceMaxGapBars,
        min_bars: balanceMinBars,
        min_width: balanceMinWidth,
        max_width: balanceMaxWidth,
        volume_profile: {
          bin_size: balanceVpBinSize,
          hvn_threshold_factor: balanceVpHvnThresholdFactor,
          lvn_threshold_factor: balanceVpLvnThresholdFactor,
          window_around_poc: balanceVpWindowAroundPoc,
          window_around_mid: balanceVpWindowAroundMid,
        },
        classification: {
          compressed_width_factor: balanceClsCompressedWidthFactor,
          wide_width_factor: balanceClsWideWidthFactor,
          asymmetry_threshold: balanceClsAsymmetryThreshold,
          center_volume_threshold: balanceClsCenterVolumeThreshold,
          edge_volume_threshold: balanceClsEdgeVolumeThreshold,
          hvn_density_threshold: balanceClsHvnDensityThreshold,
          lvn_density_threshold: balanceClsLvnDensityThreshold,
        },
      },
      breakout: {
        mode: breakoutMode,
        post_balance_bars: postBalanceBars,
        early_detection: {
          enabled: earlyDetectionEnabled,
          lower_timeframe: earlyDetectionLowerTimeframe,
          reference_timeframe: timeframe,
          max_lead_minutes: earlyDetectionMaxLeadMinutes,
          trigger: {
            type: earlyDetectionTriggerType,
            min_consecutive: earlyDetectionTriggerMinConsecutive,
            min_penetration: earlyDetectionTriggerMinPenetration,
          },
        },
        confirmation: {
          enabled: confirmationEnabled,
          max_bars: confirmationMaxBars,
          closes_required: confirmationClosesRequired,
          delta_confirmation: confirmationDeltaEnabled,
          delta_min_abs: confirmationDeltaMinAbs,
        },
        classification: {
          failure_retrace_factor: 0.4,
          retest_window: followThroughRetestWindow,
          accumulation_bars: followThroughBoundaryHoldBars,
          min_progress_factor: 1.0,
        },
        strength: {
          momentum_weight: strengthMomentumWeight,
          delta_weight: strengthDeltaWeight,
          volume_spike_weight: strengthVolumeSpikeWeight,
          volatility_weight: strengthVolatilityWeight,
          distance_from_vpoc_weight: strengthDistanceFromVpocWeight,
          hvn_lvn_break_weight: strengthHvnLvnBreakWeight,
        },
        strength_normalization: {
          enabled: strengthNormalizationEnabled,
          method: strengthNormalizationMethod,
          min_raw: strengthNormalizationMinRaw,
          max_raw: strengthNormalizationMaxRaw,
          sigmoid_k: strengthNormalizationSigmoidK,
        },
        atr: {
          enabled: atrEnabled,
          period: atrPeriod,
          normalization_factor: atrNormalizationFactor,
        },
        volatility_filter: {
          enable_filter: volatilityFilterEnabled,
          min_compression_ratio: volatilityFilterMinCompressionRatio,
          max_compression_ratio: volatilityFilterMaxCompressionRatio,
          min_stability_score: volatilityFilterMinStabilityScore,
          soft_penalty: volatilityFilterSoftPenalty,
        },
        follow_through: {
          observation_bars: followThroughObservationBars,
        },
        rotations_filter: {
          min_rotations: rotationsFilterMinRotations,
          min_directional_bias: rotationsFilterMinDirectionalBias,
        },
        rotations: {
          require_structural_rotation: breakoutRequireStructuralRotation,
        },
      },
      session_levels: {
        version: sessionLevelsVersion,
        sessions: {
          Asia: {
            open_time: asiaOpen,
            close_time: asiaClose,
            region: "Asia",
            enabled: true,
            timezone: asiaTimezone,
          },
          Europe: {
            open_time: europeOpen,
            close_time: europeClose,
            region: "Europe",
            enabled: true,
            timezone: europeTimezone,
          },
          US: {
            open_time: usaOpen,
            close_time: usaClose,
            region: "US",
            enabled: true,
            timezone: usaTimezone,
          },
        },
        volume_profile: {
          bin_size: sessionVpBinSize,
          value_area_pct: sessionVpValueAreaPct,
        },
        vwap: {
          enabled: sessionVwapEnabled,
        },
      },
    };
  }

  function buildPreviewPayload(): RootRunRequest {
    return {
      dataset: {
        instruments: [instrument],
        timeframe,
        start_date: normalizeDatasetDate(startDate),
        end_date: normalizeDatasetDate(endDate),
      },
      config: buildConfigObject(),
    };
  }

  function buildCurrentPayload(): RootRunRequest {
    if (
      instrument.trim() === "" ||
      timeframe.trim() === "" ||
      startDate.trim() === "" ||
      endDate.trim() === ""
    ) {
      throw new Error("Dataset fields are required before building the payload.");
    }

    const normalizedStartDate = normalizeDatasetDate(startDate);
    const normalizedEndDate = normalizeDatasetDate(endDate);

    if (normalizedEndDate < normalizedStartDate) {
      throw new Error("End date must be after Start date.");
    }

    return {
      dataset: {
        instruments: [instrument],
        timeframe,
        start_date: normalizedStartDate,
        end_date: normalizedEndDate,
      },
      config: buildConfigObject(),
    };
  }
  React.useEffect(() => {
    const previewPayload = buildPreviewPayload();
    setRawJson(JSON.stringify(previewPayload, null, 2));

    try {
      buildCurrentPayload();
      setRawError(null);
    } catch (e) {
      setRawError((e as Error).message);
    }
  }, [
    instrument,
    timeframe,
    startDate,
    endDate,
    mergeSameDirection,
    whipsawBars,
    minRotationAmplitude,
    balanceMinRotations,
    balanceMaxGapBars,
    balanceMinBars,
    balanceMinWidth,
    balanceMaxWidth,
    balanceVpMinTotalVolume,
    balanceVpBinSize,
    balanceVpHvnThresholdFactor,
    balanceVpLvnThresholdFactor,
    balanceVpWindowAroundPoc,
    balanceVpWindowAroundMid,
    balanceClsCompressedWidthFactor,
    balanceClsWideWidthFactor,
    balanceClsAsymmetryThreshold,
    balanceClsCenterVolumeThreshold,
    balanceClsEdgeVolumeThreshold,
    balanceClsHvnDensityThreshold,
    balanceClsLvnDensityThreshold,
    breakoutMode,
    postBalanceBars,
    breakoutBodyMargin,
    confirmationEnabled,
    confirmationMaxBars,
    confirmationClosesRequired,
    confirmationDeltaEnabled,
    confirmationDeltaMinAbs,
    sessionLevelsVersion,
    asiaOpen,
    asiaClose,
    asiaTimezone,
    europeOpen,
    europeClose,
    europeTimezone,
    usaOpen,
    usaClose,
    usaTimezone,
    sessionVpBinSize,
    sessionVpValueAreaPct,
    sessionVwapEnabled,
  ]);

  function handleApplyRawJson() {
    try {
      const parsed = JSON.parse(rawJson);

      if (typeof parsed !== "object" || parsed === null) {
        throw new Error("JSON must be an object.");
      }

      const obj = parsed as Record<string, unknown>;

      // Case 1: workspace raw payload
      if ("dataset" in obj && "config" in obj) {
        applyPayloadToForm(obj as RootRunRequest);
        setRawError(null);
        return;
      }

      // Case 2: preset JSON
      if (
        "dataset" in obj &&
        "engines" in obj &&
        typeof obj.engines === "object" &&
        obj.engines !== null &&
        "root" in (obj.engines as Record<string, unknown>)
      ) {
        const presetPayload: RootRunRequest = {
          dataset: obj.dataset as Record<string, unknown>,
          config: (obj.engines as Record<string, unknown>).root as Record<string, unknown>,
        };

        applyPayloadToForm(presetPayload);
        setRawError(null);
        return;
      }

      throw new Error(
        "JSON must contain either { dataset, config } or { api_version, dataset, engines.root }."
      );
    } catch (e) {
      setRawError((e as Error).message);
    }
  }

  function applyPayloadToForm(payload: RootRunRequest) {
    const dataset = payload.dataset as Record<string, unknown>;
    const config = payload.config as Record<string, unknown>;

    const instruments = Array.isArray(dataset.instruments)
      ? dataset.instruments
      : [];
    const dateRange =
      typeof dataset.date_range === "object" && dataset.date_range !== null
        ? (dataset.date_range as Record<string, unknown>)
        : {};

    setInstrument(typeof instruments[0] === "string" ? instruments[0] : "MNQ");
    setTimeframe(typeof dataset.timeframe === "string" ? dataset.timeframe : "1m");
    setStartDate(
      typeof dateRange.start === "string"
        ? dateRange.start
        : typeof dataset.start_date === "string"
          ? dataset.start_date
          : ""
    );
    setEndDate(
      typeof dateRange.end === "string"
        ? dateRange.end
        : typeof dataset.end_date === "string"
          ? dataset.end_date
          : ""
    );

  
    const rotations = (config.rotations ?? {}) as Record<string, unknown>;
    setRotationMethod(
      typeof rotations.rotation_method === "string"
        ? rotations.rotation_method
        : "mid_range"
    );
    setMergeSameDirection(Boolean(rotations.merge_same_direction));
    setWhipsawBars(
      typeof rotations.whipsaw_bars === "number" ? rotations.whipsaw_bars : 1
    );
    setMinRotationBars(
      typeof rotations.min_rotation_bars === "number"
        ? rotations.min_rotation_bars
        : 0
    );
    setMinRotationAmplitude(
      typeof rotations.min_rotation_amplitude === "number"
        ? rotations.min_rotation_amplitude
        : 3
    );
    setMinRotationAmplitudeMicro(
      typeof rotations.min_rotation_amplitude_micro === "number"
        ? rotations.min_rotation_amplitude_micro
        : 2
    );
    setMinRotationAmplitudeStandard(
      typeof rotations.min_rotation_amplitude_standard === "number"
        ? rotations.min_rotation_amplitude_standard
        : 3
    );
    setMinRotationAmplitudeStructural(
      typeof rotations.min_rotation_amplitude_structural === "number"
        ? rotations.min_rotation_amplitude_structural
        : 5
    );


    const balance = (config.balance ?? {}) as Record<string, unknown>;
    setBalanceMinRotations(
      typeof balance.min_rotations === "number" ? balance.min_rotations : 2
    );
    setBalanceMaxGapBars(
      typeof balance.max_gap_bars === "number" ? balance.max_gap_bars : 10
    );
    setBalanceMinBars(
      typeof balance.min_bars === "number" ? balance.min_bars : 5
    );
    setBalanceMinWidth(
      typeof balance.min_width === "number" ? balance.min_width : 0.3
    );
    setBalanceMaxWidth(
      typeof balance.max_width === "number" ? balance.max_width : 6.0
    );

    const balanceVolumeProfile = (balance.volume_profile ?? {}) as Record<
      string,
      unknown
    >;
    setBalanceVpMinTotalVolume(
      typeof balanceVolumeProfile.min_total_volume === "number"
        ? balanceVolumeProfile.min_total_volume
        : 0
    );
    setBalanceVpBinSize(
      typeof balanceVolumeProfile.bin_size === "number"
        ? balanceVolumeProfile.bin_size
        : 0.05
    );
    setBalanceVpHvnThresholdFactor(
      typeof balanceVolumeProfile.hvn_threshold_factor === "number"
        ? balanceVolumeProfile.hvn_threshold_factor
        : 1.2
    );
    setBalanceVpLvnThresholdFactor(
      typeof balanceVolumeProfile.lvn_threshold_factor === "number"
        ? balanceVolumeProfile.lvn_threshold_factor
        : 0.8
    );
    setBalanceVpWindowAroundPoc(
      typeof balanceVolumeProfile.window_around_poc === "number"
        ? balanceVolumeProfile.window_around_poc
        : 0.25
    );
    setBalanceVpWindowAroundMid(
      typeof balanceVolumeProfile.window_around_mid === "number"
        ? balanceVolumeProfile.window_around_mid
        : 0.25
    );

    const balanceClassification = (balance.classification ?? {}) as Record<
      string,
      unknown
    >;
    setBalanceClsCompressedWidthFactor(
      typeof balanceClassification.compressed_width_factor === "number"
        ? balanceClassification.compressed_width_factor
        : 0.25
    );
    setBalanceClsWideWidthFactor(
      typeof balanceClassification.wide_width_factor === "number"
        ? balanceClassification.wide_width_factor
        : 1.75
    );
    setBalanceClsAsymmetryThreshold(
      typeof balanceClassification.asymmetry_threshold === "number"
        ? balanceClassification.asymmetry_threshold
        : 0.25
    );
    setBalanceClsCenterVolumeThreshold(
      typeof balanceClassification.center_volume_threshold === "number"
        ? balanceClassification.center_volume_threshold
        : 0.35
    );
    setBalanceClsEdgeVolumeThreshold(
      typeof balanceClassification.edge_volume_threshold === "number"
        ? balanceClassification.edge_volume_threshold
        : 0.2
    );
    setBalanceClsHvnDensityThreshold(
      typeof balanceClassification.hvn_density_threshold === "number"
        ? balanceClassification.hvn_density_threshold
        : 0.2
    );
    setBalanceClsLvnDensityThreshold(
      typeof balanceClassification.lvn_density_threshold === "number"
        ? balanceClassification.lvn_density_threshold
        : 0.1
    );
        setBalanceClsEquilibriumScore(
      typeof balanceClassification.equilibrium_score === "number"
        ? String(balanceClassification.equilibrium_score)
        : ""
    );

    const breakout = (config.breakout ?? {}) as Record<string, unknown>;
    setBreakoutMode(
      typeof breakout.mode === "string" ? breakout.mode : "strict"
    );
    setPostBalanceBars(
      typeof breakout.post_balance_bars === "number"
        ? breakout.post_balance_bars
        : 5
    );
    setBreakoutBodyMargin(
      typeof breakout.breakout_body_margin === "number"
        ? breakout.breakout_body_margin
        : 0
    );

    const earlyDetection = (breakout.early_detection ?? {}) as Record<string, unknown>;

    setEarlyDetectionEnabled(Boolean(earlyDetection.enabled));
    setEarlyDetectionLowerTimeframe(
      typeof earlyDetection.lower_timeframe === "string"
        ? earlyDetection.lower_timeframe
        : "1m"
    );
    setEarlyDetectionReferenceTimeframe(
      typeof earlyDetection.reference_timeframe === "string"
        ? earlyDetection.reference_timeframe
        : "5m"
    );

    const earlyDetectionTrigger = (earlyDetection.trigger ?? {}) as Record<
      string,
      unknown
    >;

    setEarlyDetectionMaxLeadMinutes(
      typeof earlyDetection.max_lead_minutes === "number"
        ? earlyDetection.max_lead_minutes
        : 10
    );
    setEarlyDetectionTriggerType(
      typeof earlyDetectionTrigger.type === "string"
        ? earlyDetectionTrigger.type
        : "close"
    );
    setEarlyDetectionTriggerMinConsecutive(
      typeof earlyDetectionTrigger.min_consecutive === "number"
        ? earlyDetectionTrigger.min_consecutive
        : 1
    );
    setEarlyDetectionTriggerMinPenetration(
      typeof earlyDetectionTrigger.min_penetration === "number"
        ? earlyDetectionTrigger.min_penetration
        : 0
    );

        const preBreakout = (breakout.pre_breakout ?? {}) as Record<string, unknown>;
    setPreBreakoutEnabled(Boolean(preBreakout.enabled));
    setPreBreakoutVolatilityWindow(
      typeof preBreakout.volatility_window === "number"
        ? preBreakout.volatility_window
        : 20
    );
    setPreBreakoutMinVolatilityIncrease(
      typeof preBreakout.min_volatility_increase === "number"
        ? preBreakout.min_volatility_increase
        : 1.0
    );
    setPreBreakoutMaxLvnDistance(
      typeof preBreakout.max_lvn_distance === "number"
        ? preBreakout.max_lvn_distance
        : 0.25
    );
    setPreBreakoutMinDeltaBias(
      typeof preBreakout.min_delta_bias === "number"
        ? preBreakout.min_delta_bias
        : 0.15
    );
    setPreBreakoutBoundaryVolumeFactor(
      typeof preBreakout.boundary_volume_factor === "number"
        ? preBreakout.boundary_volume_factor
        : 0.5
    );
    setPreBreakoutMinScore(
      typeof preBreakout.min_score === "number"
        ? preBreakout.min_score
        : 0.55
    );
    setPreBreakoutMaxLeadMinutes(
      typeof preBreakout.max_lead_minutes === "number"
        ? preBreakout.max_lead_minutes
        : 30
    );

    const preBreakoutWeights = (preBreakout.weights ?? {}) as Record<string, unknown>;
    setPreBreakoutWeightCompression(
      typeof preBreakoutWeights.compression === "number"
        ? preBreakoutWeights.compression
        : 0.3
    );
    setPreBreakoutWeightLvnProximity(
      typeof preBreakoutWeights.lvn_proximity === "number"
        ? preBreakoutWeights.lvn_proximity
        : 0.3
    );
    setPreBreakoutWeightVolatility(
      typeof preBreakoutWeights.volatility === "number"
        ? preBreakoutWeights.volatility
        : 0.2
    );
    setPreBreakoutWeightDeltaBias(
      typeof preBreakoutWeights.delta_bias === "number"
        ? preBreakoutWeights.delta_bias
        : 0.2
    );

    const preBreakoutTrigger = (preBreakout.trigger ?? {}) as Record<string, unknown>;
    setPreBreakoutTriggerType(
      typeof preBreakoutTrigger.type === "string"
        ? preBreakoutTrigger.type
        : "close"
    );
    setPreBreakoutTriggerMinConsecutive(
      typeof preBreakoutTrigger.min_consecutive === "number"
        ? preBreakoutTrigger.min_consecutive
        : 1
    );
    setPreBreakoutTriggerMinPenetration(
      typeof preBreakoutTrigger.min_penetration === "number"
        ? preBreakoutTrigger.min_penetration
        : 0
    );

    const preBreakoutFilters = (preBreakout.filters ?? {}) as Record<string, unknown>;
    setPreBreakoutFilterMinVolumeRatio(
      typeof preBreakoutFilters.min_volume_ratio === "number"
        ? preBreakoutFilters.min_volume_ratio
        : 0.5
    );
    setPreBreakoutFilterMinVolatilityRatio(
      typeof preBreakoutFilters.min_volatility_ratio === "number"
        ? preBreakoutFilters.min_volatility_ratio
        : 0.5
    );

    const breakoutStrength = (breakout.strength ?? {}) as Record<string, unknown>;
    setStrengthMomentumWeight(
      typeof breakoutStrength.momentum_weight === "number"
        ? breakoutStrength.momentum_weight
        : 1.0
    );
    setStrengthDeltaWeight(
      typeof breakoutStrength.delta_weight === "number"
        ? breakoutStrength.delta_weight
        : 1.0
    );
    setStrengthVolumeSpikeWeight(
      typeof breakoutStrength.volume_spike_weight === "number"
        ? breakoutStrength.volume_spike_weight
        : 1.0
    );
    setStrengthVolatilityWeight(
      typeof breakoutStrength.volatility_weight === "number"
        ? breakoutStrength.volatility_weight
        : 1.0
    );
    setStrengthDistanceFromVpocWeight(
      typeof breakoutStrength.distance_from_vpoc_weight === "number"
        ? breakoutStrength.distance_from_vpoc_weight
        : 0.5
    );
    setStrengthHvnLvnBreakWeight(
      typeof breakoutStrength.hvn_lvn_break_weight === "number"
        ? breakoutStrength.hvn_lvn_break_weight
        : 0.5
    );

    const breakoutStrengthNormalization = (breakout.strength_normalization ?? {}) as Record<string, unknown>;
    setStrengthNormalizationEnabled(Boolean(breakoutStrengthNormalization.enabled));
    setStrengthNormalizationMethod(
      typeof breakoutStrengthNormalization.method === "string"
        ? breakoutStrengthNormalization.method
        : "minmax"
    );
    setStrengthNormalizationMinRaw(
      typeof breakoutStrengthNormalization.min_raw === "number"
        ? breakoutStrengthNormalization.min_raw
        : 0
    );
    setStrengthNormalizationMaxRaw(
      typeof breakoutStrengthNormalization.max_raw === "number"
        ? breakoutStrengthNormalization.max_raw
        : 6
    );
    setStrengthNormalizationSigmoidK(
      typeof breakoutStrengthNormalization.sigmoid_k === "number"
        ? breakoutStrengthNormalization.sigmoid_k
        : 1
    );

    const breakoutAtr = (breakout.atr ?? {}) as Record<string, unknown>;
    setAtrEnabled(Boolean(breakoutAtr.enabled));
    setAtrPeriod(
      typeof breakoutAtr.period === "number" ? breakoutAtr.period : 14
    );
    setAtrUseForStrength(Boolean(breakoutAtr.use_for_strength));
    setAtrNormalizationFactor(
      typeof breakoutAtr.normalization_factor === "number"
        ? breakoutAtr.normalization_factor
        : 1
    );

    const breakoutVolatilityFilter = (breakout.volatility_filter ?? {}) as Record<
      string,
      unknown
    >;
    setVolatilityFilterEnabled(Boolean(breakoutVolatilityFilter.enable_filter));
    setVolatilityFilterMinCompressionRatio(
      typeof breakoutVolatilityFilter.min_compression_ratio === "number"
        ? breakoutVolatilityFilter.min_compression_ratio
        : 0.4
    );
    setVolatilityFilterMaxCompressionRatio(
      typeof breakoutVolatilityFilter.max_compression_ratio === "number"
        ? breakoutVolatilityFilter.max_compression_ratio
        : 1.2
    );
    setVolatilityFilterMinStabilityScore(
      typeof breakoutVolatilityFilter.min_stability_score === "number"
        ? breakoutVolatilityFilter.min_stability_score
        : 0.3
    );
    setVolatilityFilterSoftPenalty(
      typeof breakoutVolatilityFilter.soft_penalty === "number"
        ? breakoutVolatilityFilter.soft_penalty
        : 0.35
    );

    const breakoutFollowThrough = (breakout.follow_through ?? {}) as Record<
      string,
      unknown
    >;
    setFollowThroughObservationBars(
      typeof breakoutFollowThrough.observation_bars === "number"
        ? breakoutFollowThrough.observation_bars
        : 15
    );
 
    setFollowThroughRetestWindow(
      typeof breakoutFollowThrough.retest_window === "number"
        ? breakoutFollowThrough.retest_window
        : 10
    );
    setFollowThroughBoundaryHoldBars(
      typeof breakoutFollowThrough.boundary_hold_bars === "number"
        ? breakoutFollowThrough.boundary_hold_bars
        : 1
    );

    const breakoutRotationsFilter = (breakout.rotations_filter ?? {}) as Record<
      string,
      unknown
    >;
    setRotationsFilterMinRotations(
      typeof breakoutRotationsFilter.min_rotations === "number"
        ? breakoutRotationsFilter.min_rotations
        : 0
    );
    setRotationsFilterMinDirectionalBias(
      typeof breakoutRotationsFilter.min_directional_bias === "number"
        ? breakoutRotationsFilter.min_directional_bias
        : 0
    );

    const breakoutRotations = (breakout.rotations ?? {}) as Record<
      string,
      unknown
    >;

    setBreakoutRequireStructuralRotation(
      Boolean(breakoutRotations.require_structural_rotation)
    );


    const confirmation = (breakout.confirmation ?? {}) as Record<
      string,
      unknown
    >;
    setConfirmationEnabled(Boolean(confirmation.enabled));
    setConfirmationMaxBars(
      typeof confirmation.max_bars === "number" ? confirmation.max_bars : 5
    );
    setConfirmationClosesRequired(
      typeof confirmation.closes_required === "number"
        ? confirmation.closes_required
        : 1
    );
    setConfirmationDeltaEnabled(Boolean(confirmation.delta_confirmation));
    setConfirmationDeltaMinAbs(
      typeof confirmation.delta_min_abs === "number"
        ? confirmation.delta_min_abs
        : 0
    );

    const sessionLevels = (config.session_levels ?? {}) as Record<
      string,
      unknown
    >;
    setSessionLevelsVersion(
      typeof sessionLevels.version === "string"
        ? sessionLevels.version
        : "1.0"
    );

    const sessions = (sessionLevels.sessions ?? {}) as Record<string, unknown>;
    const asia = ((sessions.Asia ?? sessions.asia) ?? {}) as Record<
      string,
      unknown
    >;
    const europe = ((sessions.Europe ?? sessions.europe) ?? {}) as Record<
      string,
      unknown
    >;
    const usa = ((sessions.US ?? sessions.usa) ?? {}) as Record<string, unknown>;

    setAsiaOpen(
      typeof asia.open_time === "string"
        ? asia.open_time
        : typeof asia.open === "string"
        ? asia.open
        : "00:00"
    );
    setAsiaClose(
      typeof asia.close_time === "string"
        ? asia.close_time
        : typeof asia.close === "string"
        ? asia.close
        : "08:00"
    );
    setAsiaTimezone(typeof asia.timezone === "string" ? asia.timezone : "UTC");

    setEuropeOpen(
      typeof europe.open_time === "string"
        ? europe.open_time
        : typeof europe.open === "string"
        ? europe.open
        : "08:00"
    );
    setEuropeClose(
      typeof europe.close_time === "string"
        ? europe.close_time
        : typeof europe.close === "string"
        ? europe.close
        : "14:30"
    );
    setEuropeTimezone(
      typeof europe.timezone === "string" ? europe.timezone : "UTC"
    );

    setUsaOpen(
      typeof usa.open_time === "string"
        ? usa.open_time
        : typeof usa.open === "string"
        ? usa.open
        : "14:30"
    );
    setUsaClose(
      typeof usa.close_time === "string"
        ? usa.close_time
        : typeof usa.close === "string"
        ? usa.close
        : "22:00"
    );
    setUsaTimezone(typeof usa.timezone === "string" ? usa.timezone : "UTC");

    const sessionVolumeProfile = (sessionLevels.volume_profile ?? {}) as Record<
      string,
      unknown
    >;
    setSessionVpBinSize(
      typeof sessionVolumeProfile.bin_size === "number"
        ? sessionVolumeProfile.bin_size
        : 1.0
    );
    setSessionVpValueAreaPct(
      typeof sessionVolumeProfile.value_area_pct === "number"
        ? sessionVolumeProfile.value_area_pct
        : 0.7
    );

    const sessionVwap = (sessionLevels.vwap ?? {}) as Record<string, unknown>;
    setSessionVwapEnabled(Boolean(sessionVwap.enabled));

    
  }

  async function handleSubmit() {
    if (!isValid) {
      setState((s) => ({
        ...s,
        error: "Please complete dataset fields and ensure End date is after Start date.",
      }));
      return;
    }

    const payload = buildCurrentPayload();

    setState({
      loading: true,
      error: null,
      lastRunId: null,
      artifactRef: null,
      status: "PENDING",
    });

    try {
      const response = await workspaceClient.postRootRun(payload);

      setState((s) => ({
        ...s,
        loading: true,
        lastRunId: response.run_id,
        artifactRef: response.artifact,
        status: "PENDING",
      }));

      onArtifactProduced?.(response.artifact);
    } catch (error: unknown) {
      let message = "Failed to submit root run";

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
      const saved = saveRootWorkspacePreset(presetName || "root preset", payload);
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
      const payload = loadRootWorkspacePreset(selectedPresetId) as RootRunRequest;
      applyPayloadToForm(payload);
      setRawError(null);
      setPresetStatus("Preset loaded.");
      clearPresetStatusSoon();
    } catch (error) {
      setPresetStatus((error as Error).message);
    }
  }

  function handleDeletePreset() {
    try {
      if (!selectedPresetId) return;
      deleteRootWorkspacePreset(selectedPresetId);
      setSelectedPresetId("");
      setPresetStatus("Preset deleted.");
      clearPresetStatusSoon();
    } catch (error) {
      setPresetStatus((error as Error).message);
    }
  }

  function handleExportPreset() {
    try {
      if (!selectedPresetId) return;
      const json = exportRootWorkspacePresetJson(selectedPresetId);
      setExportJson(json);
      setPresetStatus("Preset exported.");
      clearPresetStatusSoon();
    } catch (error) {
      setPresetStatus((error as Error).message);
    }
  }

  function handleImportPreset() {
    try {
      const saved = importRootWorkspacePresetJson(
      importName || "imported root preset",
      importJson
    );
    setSelectedPresetId(saved.id);
    setRawError(null);
    setPresetStatus(`Imported preset: ${saved.name}`);
    setImportName("");
    setImportJson("");
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Root Stage</CardTitle>
      </CardHeader>

      <CardContent>
        <Stack gap={20}>
          {/* ================= DESCRIPTION ================= */}
          <Stack gap={8}>
            <div className="subtle">
              Guided configuration for the Root stage. The final payload still
              matches the public contract exactly.
            </div>
          </Stack>

          {/* ================= TOP CONTROL PLANE ================= */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 1fr) 320px",
              gap: 16,
              alignItems: "stretch",
            }}
          >
            <SemanticSection
              title="Dataset"
              subtitle="Select the market data window used by the Root engine."
              badge="CORE"
            >
              <Grid columns="1fr 1fr" gap={12}>
                <FormField label="Instrument">
                  <select value={instrument} onChange={(e) => setInstrument(e.target.value)}>
                    <option value="MNQ">Micro Nasdaq (MNQ)</option>
                    <option value="NQ">Nasdaq (NQ)</option>
                    <option value="ES">S&amp;P 500 (ES)</option>
                  </select>
                </FormField>

                <FormField label="Timeframe">
                  <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                    <option value="1m">1 minute</option>
                    <option value="5m">5 minutes</option>
                    <option value="15m">15 minutes</option>
                  </select>
                </FormField>
              </Grid>

              <Grid columns="1fr 1fr" gap={12}>
                <FormField label="Start date">
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                </FormField>

                <FormField label="End date">
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </FormField>
              </Grid>
            </SemanticSection>

            <SemanticSection
              title="Saved Config"
              subtitle="Save / restore Root workspace state."
              badge="DEBUG"
            >
              <Stack gap={8}>
                {presetStatus ? <div className="pill">{presetStatus}</div> : null}

                <FormField
                  label="Preset name"
                  hint="Save the current Root form values."
                >
                  <Stack direction="row" gap={8}>
                    <input
                      value={presetName}
                      onChange={(e) => setPresetName(e.target.value)}
                      placeholder="Preset name"
                      style={{ minWidth: 0 }}
                    />

                    <Button
                      onClick={handleSavePreset}
                      disabled={!isValid}
                      variant="secondary"
                    >
                      Save
                    </Button>
                  </Stack>
                </FormField>

                <FormField
                  label="Saved preset"
                  hint="Restore or delete a saved configuration."
                >
                  <Stack gap={8}>
                    <select
                      value={selectedPresetId}
                      onChange={(e) => setSelectedPresetId(e.target.value)}
                    >
                      <option value="">Select preset</option>
                      {presets.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>

                    <Grid columns="1fr 1fr" gap={8}>
                      <Button
                        onClick={handleLoadPreset}
                        disabled={!selectedPresetId}
                        variant="secondary"
                      >
                        Load
                      </Button>

                      <Button
                        onClick={handleDeletePreset}
                        disabled={!selectedPresetId}
                        variant="secondary"
                      >
                        Delete
                      </Button>
                    </Grid>
                  </Stack>
                </FormField>
              </Stack>
            </SemanticSection>
          </div>
          </Stack>
      


          <Stack gap={12}>
            <div className="subtle">Configuration</div>

            <SemanticSection
              title="Detection Core"
              subtitle="Defines the structural rules that create Root events."
              badge="CORE"
            >
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                  gap: 12,
                }}
              >
                <SemanticBlock
                  title="Rotations validity"
                  subtitle="Controls which rotations are valid before balance and breakout detection."
                >
                  <FormField
                    label="Minimum rotation duration"
                    hint="Minimum number of bars required for a valid rotation."
                  >
                    <input
                      type="number"
                      min={1}
                      value={String(minRotationBars)}
                      onChange={(e) => setMinRotationBars(Number(e.target.value))}
                    />
                  </FormField>

                  <FormField
                    label="Minimum rotation size"
                    hint="Minimum price movement required for a valid rotation."
                  >
                    <input
                      type="number"
                      step="0.01"
                      value={String(
                        Number.isFinite(minRotationAmplitude)
                          ? minRotationAmplitude
                          : 0
                      )}
                      onChange={(e) => setMinRotationAmplitude(Number(e.target.value))}
                    />
                  </FormField>

                  <FormField
                    label="Merge same-direction rotations"
                    hint="Combines consecutive rotations moving in the same direction."
                  >
                    <label className="row" style={{ gap: 8 }}>
                      <input
                        type="checkbox"
                        checked={mergeSameDirection}
                        onChange={(e) => setMergeSameDirection(e.target.checked)}
                      />
                      <span>{mergeSameDirection ? "Enabled" : "Disabled"}</span>
                    </label>
                  </FormField>

                  <FormField
                    label="Whipsaw filter window"
                    hint="Invalidates rotation pairs that are too short or too close together."
                  >
                    <input
                      type="number"
                      min={0}
                      value={String(whipsawBars)}
                      onChange={(e) => setWhipsawBars(Number(e.target.value))}
                    />
                  </FormField>
                    </SemanticBlock>

                    <SemanticBlock
                      title="Balance formation"
                      subtitle="Defines when valid rotations become a balance zone."
                    >
                      <FormField
                        label="Minimum rotations"
                        hint="Minimum number of rotations required to form a valid balance."
                      >
                        <input
                          type="number"
                          min={1}
                          value={String(balanceMinRotations)}
                          onChange={(e) => setBalanceMinRotations(Number(e.target.value))}
                        />
                      </FormField>

                      <FormField
                        label="Maximum rotation gap"
                        hint="Largest allowed gap between rotations in the same balance."
                      >
                        <input
                          type="number"
                          min={0}
                          value={String(balanceMaxGapBars)}
                          onChange={(e) => setBalanceMaxGapBars(Number(e.target.value))}
                        />
                      </FormField>

                      <FormField
                        label="Minimum balance duration"
                        hint="Balance must last at least this many candles."
                      >
                        <input
                          type="number"
                          min={1}
                          value={String(balanceMinBars)}
                          onChange={(e) => setBalanceMinBars(Number(e.target.value))}
                        />
                      </FormField>

                      <FormField
                        label="Minimum balance width"
                        hint="Filters out balances that are too narrow."
                      >
                        <input
                          type="number"
                          step="0.01"
                          value={String(balanceMinWidth)}
                          onChange={(e) => setBalanceMinWidth(Number(e.target.value))}
                        />
                      </FormField>

                      <FormField
                        label="Maximum balance width"
                        hint="Filters out balances that are too wide."
                      >
                        <input
                          type="number"
                          step="0.01"
                          value={String(balanceMaxWidth)}
                          onChange={(e) => setBalanceMaxWidth(Number(e.target.value))}
                        />
                      </FormField>
                    </SemanticBlock>
                    <SemanticBlock
                      title="Breakout definition"
                      subtitle="Defines the structural breakout event after a valid balance."
                    >
                      <FormField
                        label="Detection mode"
                        hint="Defines what qualifies as the initial structural breakout event."
                      >
                        <select
                          value={breakoutMode}
                          onChange={(e) => setBreakoutMode(e.target.value)}
                        >
                          <option value="strict_boundary_break">Strict boundary break</option>
                          <option value="close_outside_only">Close outside only</option>
                          <option value="body_closes_at_least_50">Body closes at least 50%</option>
                        </select>
                      </FormField>

                      <FormField
                        label="Post-balance window"
                        hint="Maximum number of candles after balance completion where breakout is still considered valid."
                      >
                        <input
                          type="number"
                          min={1}
                          value={String(postBalanceBars)}
                          onChange={(e) => setPostBalanceBars(Number(e.target.value))}
                        />
                      </FormField>

                      <FormField
                        label="Breakout body margin"
                        hint="Minimum distance required beyond the balance boundary."
                      >
                        <input
                          type="number"
                          step="0.01"
                          value={String(breakoutBodyMargin)}
                          onChange={(e) => setBreakoutBodyMargin(Number(e.target.value))}
                        />
                      </FormField>
                    </SemanticBlock>

                    <SemanticBlock
                      title="Breakout confirmation"
                      subtitle="Validates the breakout after the initial trigger."
                    >
                      <FormField
                        label="Enable confirmation"
                        hint="Breakout is accepted only after confirmation conditions are met."
                      >
                        <label className="row" style={{ gap: 8 }}>
                          <input
                            type="checkbox"
                            checked={confirmationEnabled}
                            onChange={(e) => setConfirmationEnabled(e.target.checked)}
                          />
                          <span>{confirmationEnabled ? "Enabled" : "Disabled"}</span>
                        </label>
                      </FormField>

                      <FormField
                        label="Confirmation max bars"
                        hint="Maximum bars allowed for confirmation after breakout trigger."
                      >
                        <input
                          type="number"
                          min={1}
                          value={String(confirmationMaxBars)}
                          onChange={(e) => setConfirmationMaxBars(Number(e.target.value))}
                        />
                      </FormField>

                      <FormField
                        label="Closes required"
                        hint="Number of closes required to validate breakout continuation."
                      >
                        <input
                          type="number"
                          min={1}
                          value={String(confirmationClosesRequired)}
                          onChange={(e) => setConfirmationClosesRequired(Number(e.target.value))}
                        />
                      </FormField>

                      <FormField
                        label="Delta confirmation"
                        hint="Requires delta confirmation before accepting the breakout."
                      >
                        <label className="row" style={{ gap: 8 }}>
                          <input
                            type="checkbox"
                            checked={confirmationDeltaEnabled}
                            onChange={(e) => setConfirmationDeltaEnabled(e.target.checked)}
                          />
                          <span>{confirmationDeltaEnabled ? "Enabled" : "Disabled"}</span>
                        </label>
                      </FormField>

                      <FormField
                        label="Minimum delta"
                        hint="Minimum absolute delta required for confirmation."
                      >
                        <input
                          type="number"
                          step="1"
                          value={String(confirmationDeltaMinAbs)}
                          onChange={(e) => setConfirmationDeltaMinAbs(Number(e.target.value))}
                        />
                      </FormField>
                    </SemanticBlock>

                    <SemanticBlock
                      title="Follow-through observation"
                      subtitle="Defines the post-breakout observation window used to evaluate continuation."
                    >
                      <FormField
                        label="Observation bars"
                        hint="Post-breakout observation period used to validate continuation."
                      >
                        <input
                          type="number"
                          min={1}
                          value={String(followThroughObservationBars)}
                          onChange={(e) => setFollowThroughObservationBars(Number(e.target.value))}
                        />
                      </FormField>
                    </SemanticBlock>
                  </div>
                </SemanticSection>

                <Collapsible
              title="Breakout Validation & Quality"
              subtitle="Post-trigger validation, structural filters and secondary scoring layers"
              defaultOpen={true}
              compact={true}
              tone="primary"
              meta="Structural"
            >
              <Stack gap={12}>
                <div>
                  <div style={{ fontWeight: 800 }}>Structural trigger</div>
                  <div className="subtle" style={{ fontSize: "var(--font-sm)", marginTop: 4 }}>
                    These fields define the initial breakout event after a valid balance.
                  </div>
                </div>

                <Collapsible
                      title="Follow-through retest window"
                      subtitle="retest settings"
                      defaultOpen={false}
                      compact={true}
                    >
                      <Grid columns="1fr 1fr 1fr" gap={12}>
                        
                        <FormField
                          label="Retest window"
                          hint="Maximum window allowed for breakout retest behavior."
                          example="Unit: bars."
                        >
                          <input
                            type="number"
                            value={String(followThroughRetestWindow)}
                            onChange={(e) =>
                              setFollowThroughRetestWindow(Number(e.target.value))
                            }
                          />
                        </FormField>

                        <FormField
                          label="Boundary hold"
                          hint="Number of bars required to hold beyond the breakout boundary."
                          example="Unit: bars."
                        >
                          <input
                            type="number"
                            value={String(followThroughBoundaryHoldBars)}
                            onChange={(e) =>
                              setFollowThroughBoundaryHoldBars(Number(e.target.value))
                            }
                          />
                        </FormField>
                      </Grid>
                    </Collapsible>

                    <Collapsible
                      title="Rotations filter"
                      subtitle="Rotation-based quality gates for breakout candidates"
                      defaultOpen={false}
                      compact={true}
                    >
                      <Grid columns="1fr 1fr 1fr" gap={12}>
                        <FormField
                          label="Minimum rotations"
                          hint="Minimum number of rotations required for breakout candidate quality."
                        >
                          <input
                            type="number"
                            value={String(rotationsFilterMinRotations)}
                            onChange={(e) =>
                              setRotationsFilterMinRotations(Number(e.target.value))
                            }
                          />
                        </FormField>

                        <FormField
                          label="Minimum directional bias"
                          hint="Minimum directional rotation bias required."
                          example="Unit: ratio."
                        >
                          <input
                            type="number"
                            step="0.01"
                            value={String(rotationsFilterMinDirectionalBias)}
                            onChange={(e) =>
                              setRotationsFilterMinDirectionalBias(Number(e.target.value))
                            }
                          />
                        </FormField>

                        <FormField
                          label="Require structural rotation"
                          hint="Requires a structural rotation pattern before accepting the candidate."
                        >
                          <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <input
                              type="checkbox"
                              checked={breakoutRequireStructuralRotation}
                              onChange={(e) =>
                                setBreakoutRequireStructuralRotation(e.target.checked)
                              }
                            />
                            <span style={{ fontSize: 13, opacity: 0.9 }}>
                              {breakoutRequireStructuralRotation ? "Enabled" : "Disabled"}
                            </span>
                          </label>
                        </FormField>
                      </Grid>
                    </Collapsible>

                

                <Collapsible
                  title="Early detection"
                  subtitle="Lower timeframe anticipation before the structural breakout"
                  defaultOpen={false}
                  compact={true}
                >
                  <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                    <FormField
                      label="Enable early detection"
                      hint="Allows lower-timeframe anticipation before the structural breakout."
                      tone="warning"
                      note="This anticipates signals; it does not replace the structural breakout definition."
                    >
                      <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <input
                          type="checkbox"
                          checked={earlyDetectionEnabled}
                          onChange={(e) =>
                            setEarlyDetectionEnabled(e.target.checked)
                          }
                        />
                        <span style={{ fontSize: 13, opacity: 0.9 }}>
                          {earlyDetectionEnabled ? "Enabled" : "Disabled"}
                        </span>
                      </label>
                    </FormField>

                    <FormField
                      label="Lower timeframe"
                      hint="Timeframe used for anticipation."
                      example="Example: 1m."
                    >
                      <input
                        type="text"
                        value={earlyDetectionLowerTimeframe}
                        onChange={(e) =>
                          setEarlyDetectionLowerTimeframe(e.target.value)
                        }
                      />
                    </FormField>

                    <FormField
                      label="Reference timeframe"
                      hint="Base timeframe used as structural reference."
                      example="Example: 5m."
                    >
                      <input
                        type="text"
                        value={earlyDetectionReferenceTimeframe}
                        onChange={(e) =>
                          setEarlyDetectionReferenceTimeframe(e.target.value)
                        }
                      />
                    </FormField>

                    <FormField
                      label="Maximum lead time"
                      hint="Maximum allowed anticipation before the structural breakout."
                      example="Unit: minutes."
                    >
                      <input
                        type="number"
                        value={String(earlyDetectionMaxLeadMinutes)}
                        onChange={(e) =>
                          setEarlyDetectionMaxLeadMinutes(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="Trigger type"
                      hint="Activation rule used by the early signal."
                    >
                      <input
                        type="text"
                        value={earlyDetectionTriggerType}
                        onChange={(e) =>
                          setEarlyDetectionTriggerType(e.target.value)
                        }
                      />
                    </FormField>

                    <FormField
                      label="Minimum consecutive bars"
                      hint="Number of consecutive bars required for the trigger."
                      example="Unit: bars."
                    >
                      <input
                        type="number"
                        value={String(earlyDetectionTriggerMinConsecutive)}
                        onChange={(e) =>
                          setEarlyDetectionTriggerMinConsecutive(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="Minimum penetration"
                      hint="Minimum penetration required by the trigger."
                      example="Unit: price points."
                    >
                      <input
                        type="number"
                        value={String(earlyDetectionTriggerMinPenetration)}
                        onChange={(e) =>
                          setEarlyDetectionTriggerMinPenetration(Number(e.target.value))
                        }
                      />
                    </FormField>
                  </Grid>
                </Collapsible>
              
                <Collapsible
                  title="Pre-breakout"
                  subtitle="Leading signal configuration before structural breakout"
                  defaultOpen={false}
                  compact={true}
                >
                  <Stack gap={12}>
                    <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                      <FormField
                        label="Enable pre-breakout scoring"
                        hint="Computes leading signals before the structural breakout."
                        tone="warning"
                        note="This is a leading score layer; it does not replace structural breakout detection."
                      >
                        <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <input
                            type="checkbox"
                            checked={preBreakoutEnabled}
                            onChange={(e) => setPreBreakoutEnabled(e.target.checked)}
                          />
                          <span style={{ fontSize: 13, opacity: 0.9 }}>
                            {preBreakoutEnabled ? "Enabled" : "Disabled"}
                          </span>
                        </label>
                      </FormField>

                      <FormField
                        label="Volatility window"
                        hint="Lookback window used for volatility expansion."
                        example="Unit: bars."
                      >
                        <input
                          type="number"
                          value={String(preBreakoutVolatilityWindow)}
                          onChange={(e) =>
                            setPreBreakoutVolatilityWindow(Number(e.target.value))
                          }
                        />
                      </FormField>

                      <FormField
                        label="Minimum volatility increase"
                        hint="Required volatility expansion before breakout."
                        example="Unit: ratio."
                      >
                        <input
                          type="number"
                          step="0.01"
                          value={String(preBreakoutMinVolatilityIncrease)}
                          onChange={(e) =>
                            setPreBreakoutMinVolatilityIncrease(Number(e.target.value))
                          }
                        />
                      </FormField>

                      <FormField
                        label="Maximum LVN distance"
                        hint="Maximum allowed distance from low-volume area."
                        example="Unit: ratio."
                      >
                        <input
                          type="number"
                          step="0.01"
                          value={String(preBreakoutMaxLvnDistance)}
                          onChange={(e) =>
                            setPreBreakoutMaxLvnDistance(Number(e.target.value))
                          }
                        />
                      </FormField>

                      <FormField
                        label="Minimum delta bias"
                        hint="Minimum directional delta bias required."
                        example="Unit: ratio."
                      >
                        <input
                          type="number"
                          step="0.01"
                          value={String(preBreakoutMinDeltaBias)}
                          onChange={(e) =>
                            setPreBreakoutMinDeltaBias(Number(e.target.value))
                          }
                        />
                      </FormField>

                      <FormField
                        label="Boundary volume factor"
                        hint="Volume factor near the balance boundary."
                        example="Unit: ratio."
                      >
                        <input
                          type="number"
                          step="0.01"
                          value={String(preBreakoutBoundaryVolumeFactor)}
                          onChange={(e) =>
                            setPreBreakoutBoundaryVolumeFactor(Number(e.target.value))
                          }
                        />
                      </FormField>

                      <FormField
                        label="Minimum pre-breakout score"
                        hint="Minimum total leading-signal score required."
                        example="Range: 0-1."
                      >
                        <input
                          type="number"
                          step="0.01"
                          value={String(preBreakoutMinScore)}
                          onChange={(e) => setPreBreakoutMinScore(Number(e.target.value))}
                        />
                      </FormField>

                      <FormField
                        label="Maximum lead time"
                        hint="Maximum lead time allowed before breakout."
                        example="Unit: minutes."
                      >
                        <input
                          type="number"
                          value={String(preBreakoutMaxLeadMinutes)}
                          onChange={(e) =>
                            setPreBreakoutMaxLeadMinutes(Number(e.target.value))
                          }
                        />
                      </FormField>
                    </Grid>

                    <Collapsible
                      title="Weights"
                      subtitle="Relative contribution of each leading signal"
                      defaultOpen={false}
                      compact={true}
                    >
                      <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                        <FormField
                          label="Compression"
                          hint="Relative contribution of compression to the pre-breakout score."
                          example="Unit: weight."
                          tone="warning"
                          note="Weights tune scoring only; they do not create the structural breakout."
                        >
                          <input
                            type="number"
                            step="0.01"
                            value={String(preBreakoutWeightCompression)}
                            onChange={(e) =>
                              setPreBreakoutWeightCompression(Number(e.target.value))
                            }
                          />
                        </FormField>

                        <FormField
                          label="LVN proximity"
                          hint="Relative contribution of low-volume-node proximity."
                          example="Unit: weight."
                        >
                          <input
                            type="number"
                            step="0.01"
                            value={String(preBreakoutWeightLvnProximity)}
                            onChange={(e) =>
                              setPreBreakoutWeightLvnProximity(Number(e.target.value))
                            }
                          />
                        </FormField>

                        <FormField
                          label="Volatility"
                          hint="Relative contribution of volatility expansion."
                          example="Unit: weight."
                        >
                          <input
                            type="number"
                            step="0.01"
                            value={String(preBreakoutWeightVolatility)}
                            onChange={(e) =>
                              setPreBreakoutWeightVolatility(Number(e.target.value))
                            }
                          />
                        </FormField>

                        <FormField
                          label="Delta bias"
                          hint="Relative contribution of directional delta bias."
                          example="Unit: weight."
                        >
                          <input
                            type="number"
                            step="0.01"
                            value={String(preBreakoutWeightDeltaBias)}
                            onChange={(e) =>
                              setPreBreakoutWeightDeltaBias(Number(e.target.value))
                            }
                          />
                        </FormField>
                      </Grid>
                    </Collapsible>

                    <Collapsible
                      title="Trigger"
                      subtitle="Activation rule for the pre-breakout signal"
                      defaultOpen={false}
                      compact={true}
                    >
                      <Grid columns="1fr 1fr 1fr" gap={12}>
                        <FormField
                          label="Trigger type"
                          hint="Activation rule used by the pre-breakout signal."
                        >
                          <select
                            value={preBreakoutTriggerType}
                            onChange={(e) => setPreBreakoutTriggerType(e.target.value)}
                          >
                            <option value="close">Close</option>
                          </select>
                        </FormField>

                        <FormField
                          label="Minimum consecutive bars"
                          hint="Number of consecutive bars required before activation."
                          example="Unit: bars."
                        >
                          <input
                            type="number"
                            value={String(preBreakoutTriggerMinConsecutive)}
                            onChange={(e) =>
                              setPreBreakoutTriggerMinConsecutive(Number(e.target.value))
                            }
                          />
                        </FormField>

                        <FormField
                          label="Minimum penetration"
                          hint="Minimum boundary penetration required by the signal."
                          example="Unit: price points."
                        >
                          <input
                            type="number"
                            step="0.01"
                            value={String(preBreakoutTriggerMinPenetration)}
                            onChange={(e) =>
                              setPreBreakoutTriggerMinPenetration(Number(e.target.value))
                            }
                          />
                        </FormField>
                      </Grid>
                    </Collapsible>

                    <Collapsible
                      title="Filters"
                      subtitle="Additional quality thresholds for pre-breakout candidates"
                      defaultOpen={false}
                      compact={true}
                    >
                      <Grid columns="1fr 1fr" gap={12}>
                        <FormField
                          label="Minimum volume ratio"
                          hint="Minimum volume quality threshold for pre-breakout candidates."
                          example="Unit: ratio."
                        >
                          <input
                            type="number"
                            step="0.01"
                            value={String(preBreakoutFilterMinVolumeRatio)}
                            onChange={(e) =>
                              setPreBreakoutFilterMinVolumeRatio(Number(e.target.value))
                            }
                          />
                        </FormField>

                        <FormField
                          label="Minimum volatility ratio"
                          hint="Minimum volatility quality threshold for pre-breakout candidates."
                          example="Unit: ratio."
                        >
                          <input
                            type="number"
                            step="0.01"
                            value={String(preBreakoutFilterMinVolatilityRatio)}
                            onChange={(e) =>
                              setPreBreakoutFilterMinVolatilityRatio(Number(e.target.value))
                            }
                          />
                        </FormField>
                      </Grid>
                    </Collapsible>
                  </Stack>
                </Collapsible>

                <Collapsible
                  title="Strength"
                  subtitle="Relative weighting of breakout strength factors"
                  defaultOpen={false}
                  compact={true}
                >
                  <Grid columns="1fr 1fr 1fr" gap={12}>
                    <FormField
                      label="Momentum"
                      hint="Relative contribution of momentum to breakout strength."
                      example="Unit: weight."
                      tone="warning"
                      note="Strength weights tune scoring only; they do not define the structural breakout."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(strengthMomentumWeight)}
                        onChange={(e) => setStrengthMomentumWeight(Number(e.target.value))}
                      />
                    </FormField>

                    <FormField
                      label="Delta"
                      hint="Relative contribution of delta to breakout strength."
                      example="Unit: weight."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(strengthDeltaWeight)}
                        onChange={(e) => setStrengthDeltaWeight(Number(e.target.value))}
                      />
                    </FormField>

                    <FormField
                      label="Volume spike"
                      hint="Relative contribution of volume spike to breakout strength."
                      example="Unit: weight."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(strengthVolumeSpikeWeight)}
                        onChange={(e) => setStrengthVolumeSpikeWeight(Number(e.target.value))}
                      />
                    </FormField>

                    <FormField
                      label="Volatility"
                      hint="Relative contribution of volatility to breakout strength."
                      example="Unit: weight."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(strengthVolatilityWeight)}
                        onChange={(e) =>
                          setStrengthVolatilityWeight(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="Distance from VPOC"
                      hint="Relative contribution of distance from volume point of control."
                      example="Unit: weight."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(strengthDistanceFromVpocWeight)}
                        onChange={(e) =>
                          setStrengthDistanceFromVpocWeight(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="HVN/LVN break"
                      hint="Relative contribution of high/low-volume-node break behavior."
                      example="Unit: weight."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(strengthHvnLvnBreakWeight)}
                        onChange={(e) =>
                          setStrengthHvnLvnBreakWeight(Number(e.target.value))
                        }
                      />
                    </FormField>
                  </Grid>
                </Collapsible>

                    <Collapsible
                      title="Strength normalization"
                      subtitle="Normalization method for breakout strength scoring"
                      defaultOpen={false}
                      compact={true}
                    >
                      <Grid columns="1fr 1fr 1fr 1fr 1fr" gap={12}>
                        
                        <FormField
                          label="Enable normalization"
                          hint="Normalizes raw breakout strength into a comparable score."
                        >
                          <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <input
                              type="checkbox"
                              checked={strengthNormalizationEnabled}
                              onChange={(e) =>
                                setStrengthNormalizationEnabled(e.target.checked)
                              }
                            />
                            <span style={{ fontSize: 13, opacity: 0.9 }}>
                              {strengthNormalizationEnabled ? "Enabled" : "Disabled"}
                            </span>
                          </label>
                        </FormField>

                        <FormField
                          label="Method"
                          hint="Transformation applied to the raw score."
                        >
                          <select
                            value={strengthNormalizationMethod}
                            onChange={(e) =>
                              setStrengthNormalizationMethod(e.target.value)
                            }
                          >
                            <option value="minmax">Min-max</option>
                            <option value="sigmoid">Sigmoid</option>
                            <option value="tanh">Tanh</option>
                          </select>
                        </FormField>

                      </Grid>
                    </Collapsible>

                    <Collapsible
                      title="ATR"
                      subtitle="ATR-based breakout normalization settings"
                      defaultOpen={false}
                      compact={true}
                    >
                      <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                        <FormField
                          label="Enable ATR normalization"
                          hint="Use ATR as a normalization layer for breakout strength."
                        >
                          <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <input
                              type="checkbox"
                              checked={atrEnabled}
                              onChange={(e) => setAtrEnabled(e.target.checked)}
                            />
                            <span style={{ fontSize: 13, opacity: 0.9 }}>
                              {atrEnabled ? "Enabled" : "Disabled"}
                            </span>
                          </label>
                        </FormField>

                        <FormField
                          label="ATR period"
                          hint="Lookback period used for ATR calculation."
                          example="Unit: bars."
                        >
                          <input
                            type="number"
                            value={String(atrPeriod)}
                            onChange={(e) => setAtrPeriod(Number(e.target.value))}
                          />
                        </FormField>

                        <FormField
                          label="Use ATR in strength score"
                          hint="Include ATR contribution directly inside breakout strength scoring."
                        >
                          <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <input
                              type="checkbox"
                              checked={atrUseForStrength}
                              onChange={(e) => setAtrUseForStrength(e.target.checked)}
                            />
                            <span style={{ fontSize: 13, opacity: 0.9 }}>
                              {atrUseForStrength ? "Enabled" : "Disabled"}
                            </span>
                          </label>
                        </FormField>

                        <FormField
                          label="Normalization factor"
                          hint="Scaling factor applied to ATR normalization."
                          example="Unit: ratio."
                        >
                          <input
                            type="number"
                            step="0.01"
                            value={String(atrNormalizationFactor)}
                            onChange={(e) =>
                              setAtrNormalizationFactor(Number(e.target.value))
                            }
                          />
                        </FormField>
                      </Grid>
                    </Collapsible>

                    <Collapsible
                      title="Volatility filter"
                      subtitle="Filter or penalize low-quality volatility conditions"
                      defaultOpen={false}
                      compact={true}
                    >
                      <Grid columns="1fr 1fr 1fr 1fr 1fr" gap={12}>
                        <FormField
                          label="Enable volatility filter"
                          hint="Applies volatility quality gates or penalties."
                          tone="warning"
                          note="This can affect breakout quality acceptance depending on runtime behavior."
                        >
                          <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <input
                              type="checkbox"
                              checked={volatilityFilterEnabled}
                              onChange={(e) =>
                                setVolatilityFilterEnabled(e.target.checked)
                              }
                            />
                            <span style={{ fontSize: 13, opacity: 0.9 }}>
                              {volatilityFilterEnabled ? "Enabled" : "Disabled"}
                            </span>
                          </label>
                        </FormField>

                        <FormField label="Minimum compression" hint="Lower bound for acceptable compression." example="Unit: ratio.">
                          <input type="number" step="0.01" value={String(volatilityFilterMinCompressionRatio)} onChange={(e) => setVolatilityFilterMinCompressionRatio(Number(e.target.value))} />
                        </FormField>

                        <FormField label="Maximum compression" hint="Upper bound for acceptable compression." example="Unit: ratio.">
                          <input type="number" step="0.01" value={String(volatilityFilterMaxCompressionRatio)} onChange={(e) => setVolatilityFilterMaxCompressionRatio(Number(e.target.value))} />
                        </FormField>

                        <FormField label="Minimum stability" hint="Minimum required stability score." example="Unit: score.">
                          <input type="number" step="0.01" value={String(volatilityFilterMinStabilityScore)} onChange={(e) => setVolatilityFilterMinStabilityScore(Number(e.target.value))} />
                        </FormField>

                        <FormField label="Soft penalty" hint="Penalty factor applied to lower-quality volatility conditions." example="Unit: ratio.">
                          <input type="number" step="0.01" value={String(volatilityFilterSoftPenalty)} onChange={(e) => setVolatilityFilterSoftPenalty(Number(e.target.value))} />
                        </FormField>
                      </Grid>
                    </Collapsible>

                    
                        </Stack>
                    </Collapsible>

            
            <Collapsible
              title="Balance"
              subtitle="Secondary balance profile and classification thresholds"
              defaultOpen={false}
              compact={true}
              tone="primary"
              meta="Secondary"
            >
              <Stack gap={12}>
              

                <Collapsible
                  title="Volume profile"
                  subtitle="Secondary balance enrichment used to describe volume distribution"
                  defaultOpen={false}
                  compact={true}
                >
                  <Grid columns="1fr 1fr 1fr" gap={12}>
                    <FormField
                      label="Minimum total volume"
                      hint="Volume threshold for profile calculation."
                    >
                      <input
                        type="number"
                        value={String(balanceVpMinTotalVolume)}
                        onChange={(e) => setBalanceVpMinTotalVolume(Number(e.target.value))}
                      />
                    </FormField>

                    <FormField
                      label="Profile bin size"
                      hint="Price interval used to group traded volume."
                      example="Unit: price points."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceVpBinSize)}
                        onChange={(e) => setBalanceVpBinSize(Number(e.target.value))}
                      />
                    </FormField>

                    <FormField
                      label="HVN threshold factor"
                      hint="Threshold used to identify high-volume nodes."
                      example="Unit: ratio."
                    >
                      <input
                        type="number"
                        step="0.1"
                        value={String(balanceVpHvnThresholdFactor)}
                        onChange={(e) =>
                          setBalanceVpHvnThresholdFactor(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="LVN threshold factor"
                      hint="Threshold used to identify low-volume nodes."
                      example="Unit: ratio."
                    >
                      <input
                        type="number"
                        step="0.1"
                        value={String(balanceVpLvnThresholdFactor)}
                        onChange={(e) =>
                          setBalanceVpLvnThresholdFactor(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="Window around POC"
                      hint="Reference window around point of control."
                      example="Unit: price points."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceVpWindowAroundPoc)}
                        onChange={(e) => setBalanceVpWindowAroundPoc(Number(e.target.value))}
                      />
                    </FormField>

                    <FormField
                      label="Window around midpoint"
                      hint="Reference window around balance midpoint."
                      example="Unit: price points."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceVpWindowAroundMid)}
                        onChange={(e) => setBalanceVpWindowAroundMid(Number(e.target.value))}
                      />
                    </FormField>
                  </Grid>
                </Collapsible>

                <Collapsible
                  title="Classification"
                  subtitle="Secondary labels for balance shape and volume structure"
                  defaultOpen={false}
                  compact={true}
                >
                  <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                    <FormField
                      label="Compressed width"
                      hint="Classifies narrow balance structures."
                      example="Unit: ratio."
                      tone="warning"
                      note="Classification only; does not create the balance by itself."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceClsCompressedWidthFactor)}
                        onChange={(e) =>
                          setBalanceClsCompressedWidthFactor(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="Wide width"
                      hint="Classifies wide balance structures."
                      example="Unit: ratio."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceClsWideWidthFactor)}
                        onChange={(e) =>
                          setBalanceClsWideWidthFactor(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="Asymmetry"
                      hint="Classifies imbalance inside the balance range."
                      example="Unit: ratio."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceClsAsymmetryThreshold)}
                        onChange={(e) =>
                          setBalanceClsAsymmetryThreshold(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="Center volume"
                      hint="Classifies volume concentration near the center."
                      example="Unit: ratio."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceClsCenterVolumeThreshold)}
                        onChange={(e) =>
                          setBalanceClsCenterVolumeThreshold(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="Edge volume"
                      hint="Classifies volume concentration near range edges."
                      example="Unit: ratio."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceClsEdgeVolumeThreshold)}
                        onChange={(e) =>
                          setBalanceClsEdgeVolumeThreshold(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="HVN density"
                      hint="Diagnostic threshold for high-volume node density."
                      example="Unit: ratio."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceClsHvnDensityThreshold)}
                        onChange={(e) =>
                          setBalanceClsHvnDensityThreshold(Number(e.target.value))
                        }
                      />
                    </FormField>

                    <FormField
                      label="LVN density"
                      hint="Diagnostic threshold for low-volume node density."
                      example="Unit: ratio."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(balanceClsLvnDensityThreshold)}
                        onChange={(e) =>
                          setBalanceClsLvnDensityThreshold(Number(e.target.value))
                        }
                      />
                    </FormField>
                  </Grid>
                </Collapsible>
              </Stack>
            </Collapsible>
                   

            <Collapsible
              title="Session levels"
              subtitle="Session windows and profile settings"
              defaultOpen={false}
              compact={true}
            >
              <Stack gap={12}>
                <Grid columns="1fr" gap={12}>
                  <FormField
                    label="Version"
                    hint="Session configuration version identifier."
                  >
                    <input
                      type="text"
                      value={sessionLevelsVersion}
                      onChange={(e) => setSessionLevelsVersion(e.target.value)}
                    />
                  </FormField>
                </Grid>

                <Collapsible
                  title="Sessions"
                  subtitle="Trading session boundaries"
                  defaultOpen={false}
                  compact={true}
                >
                  <Grid columns="1fr 1fr 1fr" gap={12}>
                    <FormField label="Asia open" hint="Session start time." example="Format: HH:mm.">
                      <input type="text" value={asiaOpen} onChange={(e) => setAsiaOpen(e.target.value)} />
                    </FormField>

                    <FormField label="Asia close" hint="Session end time." example="Format: HH:mm.">
                      <input type="text" value={asiaClose} onChange={(e) => setAsiaClose(e.target.value)} />
                    </FormField>

                    <FormField label="Asia timezone" hint="Timezone used for this session window.">
                      <input type="text" value={asiaTimezone} onChange={(e) => setAsiaTimezone(e.target.value)} />
                    </FormField>

                    <FormField label="Europe open" hint="Session start time." example="Format: HH:mm.">
                      <input type="text" value={europeOpen} onChange={(e) => setEuropeOpen(e.target.value)} />
                    </FormField>

                    <FormField label="Europe close" hint="Session end time." example="Format: HH:mm.">
                      <input type="text" value={europeClose} onChange={(e) => setEuropeClose(e.target.value)} />
                    </FormField>

                    <FormField label="Europe timezone" hint="Timezone used for this session window.">
                      <input type="text" value={europeTimezone} onChange={(e) => setEuropeTimezone(e.target.value)} />
                    </FormField>

                    <FormField label="USA open" hint="Session start time." example="Format: HH:mm.">
                      <input type="text" value={usaOpen} onChange={(e) => setUsaOpen(e.target.value)} />
                    </FormField>

                    <FormField label="USA close" hint="Session end time." example="Format: HH:mm.">
                      <input type="text" value={usaClose} onChange={(e) => setUsaClose(e.target.value)} />
                    </FormField>

                    <FormField label="USA timezone" hint="Timezone used for this session window.">
                      <input type="text" value={usaTimezone} onChange={(e) => setUsaTimezone(e.target.value)} />
                    </FormField>
                  </Grid>
                </Collapsible>

                {/* ================= SESSION VOLUME PROFILE ================= */}
                <Collapsible
                  title="Volume profile"
                  subtitle="Session profile settings"
                  defaultOpen={false}
                  compact={true}
                >
                  <Grid columns="1fr 1fr" gap={12}>
                    <FormField
                      label="Bin size"
                      hint="Price interval used to group session volume."
                      example="Unit: price points."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(sessionVpBinSize)}
                        onChange={(e) => setSessionVpBinSize(Number(e.target.value))}
                      />
                    </FormField>

                    <FormField
                      label="Value area"
                      hint="Percentage of session volume included in value area calculation."
                      example="Unit: decimal ratio, e.g. 0.70 = 70%."
                    >
                      <input
                        type="number"
                        step="0.01"
                        value={String(sessionVpValueAreaPct)}
                        onChange={(e) => setSessionVpValueAreaPct(Number(e.target.value))}
                      />
                    </FormField>
                  </Grid>
                </Collapsible>

                {/* ================= VWAP ================= */}
                <Collapsible
                  title="VWAP"
                  subtitle="Session VWAP settings"
                  defaultOpen={false}
                  compact={true}
                >
                  <FormField
                    label="VWAP enabled"
                    hint="Enables session VWAP calculation and exposure."
                  >
                    <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <input
                        type="checkbox"
                        checked={sessionVwapEnabled}
                        onChange={(e) => setSessionVwapEnabled(e.target.checked)}
                      />
                      <span style={{ fontSize: 13, opacity: 0.9 }}>
                        {sessionVwapEnabled ? "Enabled" : "Disabled"}
                      </span>
                    </label>
                  </FormField>
                </Collapsible>

                            </Stack>
          </Collapsible>

          {/* ================= DEBUG PAYLOAD ================= */}
          <Collapsible
            title="Payload"
            subtitle="Runtime JSON"
            defaultOpen={false}
            compact={true}
            meta="Debug"
          >
            <textarea
              value={JSON.stringify(buildPreviewPayload(), null, 2)}
              readOnly
              rows={8}
              style={{
                width: "100%",
                fontFamily: "monospace",
                fontSize: 11,
                opacity: 0.85,
              }}
            />
          </Collapsible>
        </Stack>
      </CardContent>

      <CardFooter>
        <Stack gap={8}>
          <Stack direction="row" gap={8}>
            <Button onClick={handleSubmit} disabled={!isValid || state.loading}>
              {state.loading ? "Running..." : "Run Root Stage"}
            </Button>

            <Button
              onClick={handleViewResults}
              variant="secondary"
              disabled={!state.artifactRef}
            >
              View Results
            </Button>
          </Stack>

          <StepStatusBanner
            status={state.status}
            loading={state.loading}
            error={state.error}
            lastRunId={state.lastRunId}
          />

          {state.artifactRef ? (
            <div style={{ marginTop: 2 }}>
              <ArtifactRefBadge artifactRef={state.artifactRef} origin="root" copyable />
            </div>
          ) : null}
        </Stack>
      </CardFooter>
    </Card>
  );
}