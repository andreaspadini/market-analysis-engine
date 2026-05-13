export type ArtifactRefInput = {
  tool_id: string;
  fingerprint: string;
};

export type WorkspaceTerminalStatus =
  | "SUCCEEDED"
  | "FAILED"
  | "NOT_FOUND";

export type WorkspaceStatus =
  | "IDLE"
  | "PENDING"
  | "RUNNING"
  | WorkspaceTerminalStatus;

export type RootRunRequest = {
  dataset: Record<string, unknown>;
  config: Record<string, unknown>;
};

export type RootRunSubmitResponse = {
  run_id: string;
  artifact: ArtifactRefInput | null;
};

export type StatisticalRunRequest = {
  root_artifact_ref: ArtifactRefInput;
  config: Record<string, unknown>;
};

export type StatisticalRunSubmitResponse = {
  run_id: string;
  artifact: ArtifactRefInput | null;
};

export type BucketizersConfig = {
  volume_bucket: {
    very_low_max: number;
    low_max: number;
    medium_max: number;
    high_max: number;
  };

  delta_bucket: {
    delta_0_100_max: number;
    delta_100_300_max: number;
    delta_300_600_max: number;
    delta_600_1000_max: number;
  };

  compression_bucket: {
    ultra_compressed_max: number;
    compressed_max: number;
    balanced_max: number;
    expanded_max: number;
  };

  atr_bucket: {
    atr_0_0_5_max: number;
    atr_0_5_1_0_max: number;
    atr_1_0_1_5_max: number;
    atr_1_5_2_5_max: number;
  };

  pre_bo_bucket: {
    pre_neg_max: number;
    pre_0_2_max: number;
    pre_2_4_max: number;
    pre_4_6_max: number;
  };

  time_bucket: {
    tb_00_04_max: number;
    tb_04_08_max: number;
    tb_08_12_max: number;
    tb_12_16_max: number;
    tb_16_20_max: number;
    tb_20_24_max: number;
  };
};

export type QueryRunRequest = {
  statistical_artifact_ref: ArtifactRefInput;
  query: {
    intent_id: string;
    params: Record<string, unknown>;
  };
};

export type QueryRunSubmitResponse = {
  run_id: string;
  artifact: ArtifactRefInput | null;
};

export type PatternRunRequest = {
  dataset: Record<string, unknown>;
  config: Record<string, unknown>;
};

export type PatternRunSubmitResponse = {
  run_id: string;
  artifact: ArtifactRefInput | null;
};