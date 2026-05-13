// packages/gui/src/features/runCreation/state/useRunCreationState.ts
import { useCallback, useMemo, useState } from "react";

/**
 * G2.3 / A1 — DTO State Extension
 *
 * Stato in memoria conforme a PipelineParametersV1 (contract strict-by-default).
 *
 * Boundary invariants:
 * - NON includere: engine_version, run_id, config_hash, artifact_identity_hash, manifest, storage_path,
 *   planner_state, runtime_trace, ecc.
 * - NON fare validazione dominio / planner logic
 *
 * Struttura canonica top-level:
 * {
 *   api_version: "1.0",
 *   dataset: { instruments, timeframe, date_range: {start,end} },
 *   engines: { root, statistical, pattern, query }
 * }
 */

export type ApiVersionV1 = "1.0";

/** -------------------------
 * Dataset
 * ------------------------ */
export type DatasetBlock = {
  instruments: string[];
  timeframe: string;
  date_range: {
    start: string; // ISO date string (no validation here)
    end: string; // ISO date string (no validation here)
  };
};

/** -------------------------
 * Root engine (canonical from config.yaml, excluding engine_version)
 * ------------------------ */
export type RootEngineBlock = {
  engine: {
    mode: string;
    data_path: string;
    version: string;
  };

  rotations: {
    rotation_method: string;
    merge_same_direction: boolean;
    whipsaw_bars: number;
    min_rotation_amplitude: number;
    min_rotation_amplitude_micro: number;
    min_rotation_amplitude_standard: number;
    min_rotation_amplitude_structural: number;
    min_rotation_bars: number;
    max_rotation_asymmetry_pct: number;
    rotation_amplitude_tolerance: number;
  };

  duration: {
    min_bars_micro: number;
    min_bars_standard: number;
    min_bars_structural: number;
    max_bars_balance: number;
    ignore_time_gaps: boolean;
  };

  volume: {
    volume_distribution_type: string;
    hvn_lvn_ratio_min: number;
    min_internal_volume_pct: number;
  };

  delta: {
    delta_max_fraction_volume: number;
    delta_rotation_alternation_required: boolean;
    aggressive_volume_threshold: number;
  };

  balance: {
    min_rotations: number;
    max_gap_bars: number;
    min_bars: number;
    min_width: number;
    max_width: number;

    volume_profile: {
      min_total_volume: number;
      bin_size: number;
      hvn_threshold_factor: number;
      lvn_threshold_factor: number;
      window_around_poc: number;
      window_around_mid: number;
    };

    classification: {
      compressed_width_factor: number;
      wide_width_factor: number;
      asymmetry_threshold: number;
      center_volume_threshold: number;
      edge_volume_threshold: number;
      hvn_density_threshold: number;
      lvn_density_threshold: number;

      equilibrium_score: number;

      w_width: number;
      w_asymmetry: number;
      w_center_volume: number;
      w_hvn_density: number;
      w_lvn_density: number;
      w_edge_volume: number;

      asymmetry_ref: number;
      center_volume_ref: number;
      hvn_density_ref: number;
      lvn_density_ref: number;
      edge_volume_ref: number;
    };
  };

  breakout: {
    early_detection: {
      enabled: boolean;
      lower_timeframe: string;
      reference_timeframe: string;
    };

    pre_breakout: {
      enabled: boolean;
      volatility_window: number;
      min_volatility_increase: number;
      max_lvn_distance: number;
      min_delta_bias: number;
      boundary_volume_factor: number;
      min_score: number;

      weights: {
        compression: number;
        lvn_proximity: number;
        volatility: number;
        delta_bias: number;
      };

      trigger: {
        type: string;
        min_consecutive: number;
        min_penetration: number;
      };

      filters: {
        min_volume_ratio: number;
        min_volatility_ratio: number;
      };

      max_lead_minutes: number;
    };

    mode: string;
    post_balance_bars: number;
    breakout_body_margin: number;

    hybrid: {
      body_ratio_required: number;
      use_previous_body: boolean;
    };

    confirmation: {
      enabled: boolean;
      max_bars: number;
      closes_required: number;
      volume_confirmation: boolean;
      delta_confirmation: boolean;
      delta_min_abs: number;
    };

    classification: {
      max_reentry_fraction: number;
      failed_max_bars: number;
      retest_tolerance: number;
      retest_min_hold_bars: number;
      dirty_wick_fraction: number;
      min_follow_through: number;
    };

    classification_labels: {
      dirty_if_wick_fraction_above: number;
      failed_if_no_follow_after_bars: number;
      clean_if_follow_through_above: number;
      retest_if_pullback_with_hold: number;
    };

    strength: {
      momentum_weight: number;
      delta_weight: number;
      volume_spike_weight: number;
      volatility_weight: number;
      distance_from_vpoc_weight: number;
      hvn_lvn_break_weight: number;
    };

    strength_normalization: {
      enabled: boolean;
      method: string;
      min_raw: number;
      max_raw: number;
      sigmoid_k: number;
    };

    atr: {
      enabled: boolean;
      period: number;
      use_for_strength: boolean;
      normalization_factor: number;
    };

    volatility_filter: {
      enable_filter: boolean;
      min_compression_ratio: number;
      max_compression_ratio: number;
      min_stability_score: number;
      soft_penalty: number;
    };

    follow_through: {
      observation_bars: number;
      retracement_factor: number;
      retest_window: number;
      boundary_hold_bars: number;
    };

    rotations_filter: {
      min_rotations: number;
      min_directional_bias: number;
    };
  };

  breakout_ranking: {
    enabled: boolean;
    use_normalized: boolean;
    top_n: number;
    group_by_session: boolean;
  };

  export: {
    enabled: boolean;
    format: string;
    output_dir: string;
    filename_prefix: string;
    include_timestamp: boolean;
  };

  session_levels: {
    version: string;

    sessions: {
      asia: { open: string; close: string; timezone: string };
      europe: { open: string; close: string; timezone: string };
      usa: { open: string; close: string; timezone: string };
    };

    volume_profile: {
      bin_size: number;
      value_area_pct: number;
    };

    vwap: { enabled: boolean };

    export: {
      enabled: boolean;
      output_dir: string;
      filename_prefix: string;
    };
  };
};

/** -------------------------
 * Statistical engine (canonical keys)
 * ------------------------ */
export type StatisticalConfigBlock = {
  version: string;

  targets: {
    primary: { name: string; atr_multiplier: number };
    secondary: { name: string; ticks: number };
  };

  target_scans: {
    success_ATR_scan: {
      base_target: string;
      x_scan: { start: number; end: number; step: number };
    };
  };

  tick_scan: {
    tick_size: number;
    success_ticks: { levels: number[] };
    clean_ticks: { levels: number[] };
  };

  clean_quant: {
    base_target: string;
    atr_multiplier: number;
    clean_atr_threshold: number;
  };

  buckets: {
    atr: { low: number[]; mid: number[]; high: number[] };
    volatility: { low: number[]; mid: number[]; high: number[] };
    delta: { low: number[]; mid: number[]; high: number[] };
    compression: { compress: number[]; neutral: number[]; stretchy: number[] };
    pre_breakout_score: { low: number[]; mid: number[]; high: number[] };
  };

  bucketizers?: {
    compression_bucket?: {
      ultra_compressed_max: number;
      compressed_max: number;
      balanced_max: number;
      expanded_max: number;
    };
    delta_bucket?: {
      delta_0_100_max: number;
      delta_100_300_max: number;
      delta_300_600_max: number;
      delta_600_1000_max: number;
    };
    volume_bucket?: {
      very_low_max: number;
      low_max: number;
      medium_max: number;
      high_max: number;
    };
    atr_bucket?: {
      atr_0_0_5_max: number;
      atr_0_5_1_0_max: number;
      atr_1_0_1_5_max: number;
      atr_1_5_2_5_max: number;
    };
    pre_bo_bucket?: {
      pre_neg_max: number;
      pre_0_2_max: number;
      pre_2_4_max: number;
      pre_4_6_max: number;
    };
    time_bucket?: {
      tb_00_04_max: number;
      tb_04_08_max: number;
      tb_08_12_max: number;
      tb_12_16_max: number;
      tb_16_20_max: number;
      tb_20_24_max: number;
    };
  };

  // dynamic keys
  sessions: Record<string, [string, string]>;
  time_buckets: Record<string, [string, string]>;

  edge_score: {
    weak: number[];
    medium: number[];
    strong: number[];
  };

  ml: {
    numeric_features: string[];
    categorical_features: string[];
    target: string;
    train_ratio: number;
  };

  statistics: {
    enabled_blocks: string[];
    min_sample_size: number;
  };
};

export type StatisticalMappingBlock = {
  version: string;

  core_fields: Record<string, string>;
  directional: Record<string, string>;
  prices: Record<string, string>;
  balance_structure: Record<string, string>;
  volume_delta_volatility: Record<string, string>;
  strength_follow: Record<string, string>;
  rotations: Record<string, string>;
  pre_breakout: Record<string, string>;
  ranking: Record<string, string>;
  meta: Record<string, string>;
};

export type StatisticalSessionsDefBlock = {
  version: string;
  timezone: string;

  sessions: Record<string, { start: string; end: string }>;
  fallback_session: string;
};

export type StatisticalTargetsDefBlock = {
  version: string;

  base_metrics: {
    max_excursion_source: { field: string; key: string };
    atr_source: { field: string };
  };

  targets: Record<
    string,
    {
      description: string;
      type: string;
      logic: string;
      enabled: boolean;

      threshold_type?: string;
      clean_label?: string;
      x_scan?: { start: number; end: number; step: number };
    }
  >;

  failure_definition: {
    field: string;
    true_value: string;
  };
};

export type StatisticalEngineBlock = {
  config: StatisticalConfigBlock;
  mapping: StatisticalMappingBlock;
  sessions_def: StatisticalSessionsDefBlock;
  targets_def: StatisticalTargetsDefBlock;
};

/** -------------------------
 * Pattern engine (canonical keys)
 * ------------------------ */
export type ManualPatternDirection = "bullish" | "bearish" | "neutral" | "any";
export type ManualPatternClosePosition = "near_high" | "near_low" | "mid" | "any";

export type ManualPatternCandle = {
  index: number;
  direction: ManualPatternDirection;
  body_ticks: number;
  upper_wick_ticks: number;
  lower_wick_ticks: number;
  volume: number | null;
  delta: number | null;
  close_position: ManualPatternClosePosition;
};

export type PatternEngineBlock = {
  mode: "manual_template";
  tick_size: number;
  length_bars: number;

  tolerance: {
    body_ticks_pct: number;
    wick_ticks_pct: number;
    volume_pct: number;
    delta_pct: number;
  };

  candles: ManualPatternCandle[];

  visualization: {
    context_before_bars: number;
    context_after_bars: number;
  };
};

/** -------------------------
 * Query engine (canonical keys)
 * ------------------------ */
export type QueryEngineBlock = {
  intent_id: string;
  params: Record<string, unknown>;
};

export type EnginesBlock = {
  root: RootEngineBlock;
  statistical: StatisticalEngineBlock;
  pattern: PatternEngineBlock;
  query: QueryEngineBlock;
};

export type PipelineParametersV1 = {
  api_version: ApiVersionV1;
  dataset: DatasetBlock;
  engines: EnginesBlock;
};

export type RunCreationState = {
  pipelineParametersV1: PipelineParametersV1;

  // Dataset setters
  setDataset: (patch: Partial<DatasetBlock>) => void;
  setDatasetField: (path: string, value: unknown) => void;

  // Engine setters
  setEngine: <K extends keyof EnginesBlock>(engine: K, next: EnginesBlock[K]) => void;
  setEngineField: <K extends keyof EnginesBlock>(engine: K, path: string, value: unknown) => void;

  // Query convenience setters
  setQueryIntentId: (intentId: string) => void;
  setQueryParam: (key: string, value: unknown) => void;
  removeQueryParam: (key: string) => void;

  ui: {
    datasetIncomplete: boolean;
    missingDatasetReasons: string[];
  };

  replacePipelineParametersV1: (dto: PipelineParametersV1) => void;
  reset: () => void;
};

function defaultPipelineParametersV1(): PipelineParametersV1 {
  return {
    api_version: "1.0",
    dataset: {
      instruments: [],
      timeframe: "",
      date_range: { start: "", end: "" },
    },
    engines: {
      root: {
        engine: { mode: "", data_path: "", version: "" },
        rotations: {
          rotation_method: "",
          merge_same_direction: false,
          whipsaw_bars: 0,
          min_rotation_amplitude: 0,
          min_rotation_amplitude_micro: 0,
          min_rotation_amplitude_standard: 0,
          min_rotation_amplitude_structural: 0,
          min_rotation_bars: 0,
          max_rotation_asymmetry_pct: 0,
          rotation_amplitude_tolerance: 0,
        },
        duration: {
          min_bars_micro: 0,
          min_bars_standard: 0,
          min_bars_structural: 0,
          max_bars_balance: 0,
          ignore_time_gaps: false,
        },
        volume: {
          volume_distribution_type: "",
          hvn_lvn_ratio_min: 0,
          min_internal_volume_pct: 0,
        },
        delta: {
          delta_max_fraction_volume: 0,
          delta_rotation_alternation_required: false,
          aggressive_volume_threshold: 0,
        },
        balance: {
          min_rotations: 0,
          max_gap_bars: 0,
          min_bars: 0,
          min_width: 0,
          max_width: 0,
          volume_profile: {
            min_total_volume: 0,
            bin_size: 0,
            hvn_threshold_factor: 0,
            lvn_threshold_factor: 0,
            window_around_poc: 0,
            window_around_mid: 0,
          },
          classification: {
            compressed_width_factor: 0,
            wide_width_factor: 0,
            asymmetry_threshold: 0,
            center_volume_threshold: 0,
            edge_volume_threshold: 0,
            hvn_density_threshold: 0,
            lvn_density_threshold: 0,
            equilibrium_score: 0,
            w_width: 0,
            w_asymmetry: 0,
            w_center_volume: 0,
            w_hvn_density: 0,
            w_lvn_density: 0,
            w_edge_volume: 0,
            asymmetry_ref: 0,
            center_volume_ref: 0,
            hvn_density_ref: 0,
            lvn_density_ref: 0,
            edge_volume_ref: 0,
          },
        },
        breakout: {
          early_detection: {
            enabled: false,
            lower_timeframe: "",
            reference_timeframe: "",
          },
          pre_breakout: {
            enabled: false,
            volatility_window: 0,
            min_volatility_increase: 0,
            max_lvn_distance: 0,
            min_delta_bias: 0,
            boundary_volume_factor: 0,
            min_score: 0,
            weights: {
              compression: 0,
              lvn_proximity: 0,
              volatility: 0,
              delta_bias: 0,
            },
            trigger: { type: "", min_consecutive: 0, min_penetration: 0 },
            filters: { min_volume_ratio: 0, min_volatility_ratio: 0 },
            max_lead_minutes: 0,
          },
          mode: "",
          post_balance_bars: 0,
          breakout_body_margin: 0,
          hybrid: { body_ratio_required: 0, use_previous_body: false },
          confirmation: {
            enabled: false,
            max_bars: 0,
            closes_required: 0,
            volume_confirmation: false,
            delta_confirmation: false,
            delta_min_abs: 0,
          },
          classification: {
            max_reentry_fraction: 0,
            failed_max_bars: 0,
            retest_tolerance: 0,
            retest_min_hold_bars: 0,
            dirty_wick_fraction: 0,
            min_follow_through: 0,
          },
          classification_labels: {
            dirty_if_wick_fraction_above: 0,
            failed_if_no_follow_after_bars: 0,
            clean_if_follow_through_above: 0,
            retest_if_pullback_with_hold: 0,
          },
          strength: {
            momentum_weight: 0,
            delta_weight: 0,
            volume_spike_weight: 0,
            volatility_weight: 0,
            distance_from_vpoc_weight: 0,
            hvn_lvn_break_weight: 0,
          },
          strength_normalization: {
            enabled: false,
            method: "",
            min_raw: 0,
            max_raw: 0,
            sigmoid_k: 0,
          },
          atr: { enabled: false, period: 0, use_for_strength: false, normalization_factor: 0 },
          volatility_filter: {
            enable_filter: false,
            min_compression_ratio: 0,
            max_compression_ratio: 0,
            min_stability_score: 0,
            soft_penalty: 0,
          },
          follow_through: {
            observation_bars: 0,
            retracement_factor: 0,
            retest_window: 0,
            boundary_hold_bars: 0,
          },
          rotations_filter: { min_rotations: 0, min_directional_bias: 0 },
        },
        breakout_ranking: {
          enabled: false,
          use_normalized: false,
          top_n: 0,
          group_by_session: false,
        },
        export: {
          enabled: false,
          format: "",
          output_dir: "",
          filename_prefix: "",
          include_timestamp: false,
        },
        session_levels: {
          version: "",
          sessions: {
            asia: { open: "", close: "", timezone: "" },
            europe: { open: "", close: "", timezone: "" },
            usa: { open: "", close: "", timezone: "" },
          },
          volume_profile: { bin_size: 0, value_area_pct: 0 },
          vwap: { enabled: false },
          export: { enabled: false, output_dir: "", filename_prefix: "" },
        },
      },

      statistical: {
        config: {
          version: "",
          targets: {
            primary: { name: "", atr_multiplier: 0 },
            secondary: { name: "", ticks: 0 },
          },
          target_scans: {
            success_ATR_scan: {
              base_target: "",
              x_scan: { start: 0, end: 0, step: 0 },
            },
          },
          tick_scan: {
            tick_size: 0,
            success_ticks: { levels: [] },
            clean_ticks: { levels: [] },
          },
          clean_quant: { base_target: "", atr_multiplier: 0, clean_atr_threshold: 0 },
          buckets: {
            atr: { low: [], mid: [], high: [] },
            volatility: { low: [], mid: [], high: [] },
            delta: { low: [], mid: [], high: [] },
            compression: { compress: [], neutral: [], stretchy: [] },
            pre_breakout_score: { low: [], mid: [], high: [] },
          },
          bucketizers: {
            compression_bucket: {
              ultra_compressed_max: 0.5,
              compressed_max: 1.0,
              balanced_max: 1.5,
              expanded_max: 2.5,
            },
            delta_bucket: {
              delta_0_100_max: 100,
              delta_100_300_max: 300,
              delta_300_600_max: 600,
              delta_600_1000_max: 1000,
            },
            volume_bucket: {
              very_low_max: 50,
              low_max: 150,
              medium_max: 400,
              high_max: 800,
            },
            atr_bucket: {
              atr_0_0_5_max: 0.5,
              atr_0_5_1_0_max: 1.0,
              atr_1_0_1_5_max: 1.5,
              atr_1_5_2_5_max: 2.5,
            },
            pre_bo_bucket: {
              pre_neg_max: 0.0,
              pre_0_2_max: 2.0,
              pre_2_4_max: 4.0,
              pre_4_6_max: 6.0,
            },
            time_bucket: {
              tb_00_04_max: 4.0,
              tb_04_08_max: 8.0,
              tb_08_12_max: 12.0,
              tb_12_16_max: 16.0,
              tb_16_20_max: 20.0,
              tb_20_24_max: 24.0,
            },
          },
          sessions: {},
          time_buckets: {},
          edge_score: { weak: [], medium: [], strong: [] },
          ml: {
            numeric_features: [],
            categorical_features: [],
            target: "",
            train_ratio: 0,
          },
          statistics: { enabled_blocks: [], min_sample_size: 0 },
        },
        mapping: {
          version: "",
          core_fields: {},
          directional: {},
          prices: {},
          balance_structure: {},
          volume_delta_volatility: {},
          strength_follow: {},
          rotations: {},
          pre_breakout: {},
          ranking: {},
          meta: {},
        },
        sessions_def: {
          version: "",
          timezone: "",
          sessions: {},
          fallback_session: "",
        },
        targets_def: {
          version: "",
          base_metrics: {
            max_excursion_source: { field: "", key: "" },
            atr_source: { field: "" },
          },
          targets: {},
          failure_definition: { field: "", true_value: "" },
        },
      },

      pattern: {
        mode: "manual_template",
        tick_size: 0.25,
        length_bars: 2,
        tolerance: {
          body_ticks_pct: 0.5,
          wick_ticks_pct: 1.0,
          volume_pct: 1.0,
          delta_pct: 1.0,
        },
        candles: [
          {
            index: 1,
            direction: "bullish",
            body_ticks: 10,
            upper_wick_ticks: 2,
            lower_wick_ticks: 4,
            volume: 1200,
            delta: 300,
            close_position: "near_high",
          },
          {
            index: 2,
            direction: "bearish",
            body_ticks: 8,
            upper_wick_ticks: 3,
            lower_wick_ticks: 2,
            volume: 900,
            delta: -150,
            close_position: "near_low",
          },
        ],
        visualization: {
          context_before_bars: 20,
          context_after_bars: 40,
        },
      },

      query: { intent_id: "", params: {} },
    },
  };
}

/**
 * Minimal immutable path-setter.
 * Standard: dot-path only.
 * We normalize possible bracket path `a[0].b` -> `a.0.b` to avoid divergence.
 *
 * - Supports dot paths: "date_range.start", "rotations.whipsaw_bars"
 * - Supports array indices via dot: "instruments.0"
 * - No validation (A1 boundary)
 */
function setAtPath<T extends unknown>(input: T, path: string, value: unknown): T {
  const normalizedPath = path.replace(/\[(\d+)\]/g, ".$1").replace(/^\./, "");
  const parts = normalizedPath.split(".").filter(Boolean);
  if (parts.length === 0) return input;

  const root: any = Array.isArray(input) ? [...(input as any)] : { ...(input as any) };
  let cursor: any = root;

  for (let i = 0; i < parts.length; i++) {
    const key = parts[i]!;
    const isLast = i === parts.length - 1;
    const idx = Number.isFinite(Number(key)) ? Number(key) : null;

    if (isLast) {
      if (idx !== null && Array.isArray(cursor)) cursor[idx] = value;
      else cursor[key] = value;
      break;
    }

    const nextKey = parts[i + 1]!;
    const nextIsIndex = Number.isFinite(Number(nextKey));

    if (idx !== null && Array.isArray(cursor)) {
      const currentVal = cursor[idx];
      const nextContainer =
        currentVal == null
          ? nextIsIndex
            ? []
            : {}
          : Array.isArray(currentVal)
            ? [...currentVal]
            : typeof currentVal === "object"
              ? { ...currentVal }
              : nextIsIndex
                ? []
                : {};
      cursor[idx] = nextContainer;
      cursor = nextContainer;
    } else {
      const currentVal = cursor[key];
      const nextContainer =
        currentVal == null
          ? nextIsIndex
            ? []
            : {}
          : Array.isArray(currentVal)
            ? [...currentVal]
            : typeof currentVal === "object"
              ? { ...currentVal }
              : nextIsIndex
                ? []
                : {};
      cursor[key] = nextContainer;
      cursor = nextContainer;
    }
  }

  return root as T;
}

export function useRunCreationState(): RunCreationState {
  const [pipelineParametersV1, setPipelineParametersV1] = useState<PipelineParametersV1>(
    () => defaultPipelineParametersV1()
  );

  const setDataset = useCallback((patch: Partial<DatasetBlock>) => {
    setPipelineParametersV1((prev) => ({
      ...prev,
      dataset: { ...prev.dataset, ...patch },
    }));
  }, []);

  const setDatasetField = useCallback((path: string, value: unknown) => {
    setPipelineParametersV1((prev) => ({
      ...prev,
      dataset: setAtPath(prev.dataset, path, value),
    }));
  }, []);

  const setEngine = useCallback(<K extends keyof EnginesBlock>(engine: K, next: EnginesBlock[K]) => {
    setPipelineParametersV1((prev) => ({
      ...prev,
      engines: { ...prev.engines, [engine]: next },
    }));
  }, []);

  const setEngineField = useCallback(
    <K extends keyof EnginesBlock>(engine: K, path: string, value: unknown) => {
      setPipelineParametersV1((prev) => ({
        ...prev,
        engines: {
          ...prev.engines,
          [engine]: setAtPath(prev.engines[engine], path, value),
        },
      }));
    },
    []
  );

  const setQueryIntentId = useCallback((intentId: string) => {
    setPipelineParametersV1((prev) => ({
      ...prev,
      engines: {
        ...prev.engines,
        query: { ...prev.engines.query, intent_id: intentId },
      },
    }));
  }, []);

  const setQueryParam = useCallback((key: string, value: unknown) => {
    setPipelineParametersV1((prev) => ({
      ...prev,
      engines: {
        ...prev.engines,
        query: {
          ...prev.engines.query,
          params: { ...prev.engines.query.params, [key]: value },
        },
      },
    }));
  }, []);

  const removeQueryParam = useCallback((key: string) => {
    setPipelineParametersV1((prev) => {
      const { [key]: _removed, ...rest } = prev.engines.query.params;
      return {
        ...prev,
        engines: {
          ...prev.engines,
          query: { ...prev.engines.query, params: rest },
        },
      };
    });
  }, []);

  const replacePipelineParametersV1 = useCallback((dto: PipelineParametersV1) => {
    // A1 boundary: no validation; A3 will enforce strict preset conformance.
    setPipelineParametersV1(dto);
  }, []);

  const reset = useCallback(() => {
    setPipelineParametersV1(defaultPipelineParametersV1());
  }, []);

  const missingDatasetReasons = useMemo(() => {
    const reasons: string[] = [];
    const dataset = pipelineParametersV1.dataset;

    if (dataset.instruments.length === 0) reasons.push("Missing instruments");
    if (!dataset.timeframe.trim()) reasons.push("Missing timeframe");
    if (!dataset.date_range.start.trim()) reasons.push("Missing start date");
    if (!dataset.date_range.end.trim()) reasons.push("Missing end date");

    return reasons;
  }, [pipelineParametersV1.dataset]);

  const datasetIncomplete = missingDatasetReasons.length > 0;

  return useMemo(
    () => ({
      pipelineParametersV1,
      ui: {
        datasetIncomplete,
        missingDatasetReasons,
      },
      setDataset,
      setDatasetField,
      setEngine,
      setEngineField,
      setQueryIntentId,
      setQueryParam,
      removeQueryParam,
      replacePipelineParametersV1,
      reset,
    }),
    [
      pipelineParametersV1,
      datasetIncomplete,
      missingDatasetReasons,
      setDataset,
      setDatasetField,
      setEngine,
      setEngineField,
      setQueryIntentId,
      setQueryParam,
      removeQueryParam,
      replacePipelineParametersV1,
      reset,
    ]
  );
}