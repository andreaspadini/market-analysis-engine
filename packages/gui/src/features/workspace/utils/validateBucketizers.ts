import type { BucketizersConfig } from "../model/workspaceTypes";

export type BucketWarning = {
  domain: string;
  field: string;
  message: string;
  severity: "warning" | "error";
};

// ===================== FIELD KEY FORMAT =====================
// domain.field_key (es: volume.low_max)

export function validateBucketizers(
  config: BucketizersConfig
): BucketWarning[] {
  const warnings: BucketWarning[] = [];

  // ===================== HELPERS =====================
  const isMonotonic = (values: number[]) => {
    for (let i = 1; i < values.length; i++) {
      if (values[i] <= values[i - 1]) return false;
    }
    return true;
  };

  const pushError = (
    domain: string,
    field: string,
    message: string
  ) => {
    warnings.push({
      domain,
      field,
      severity: "error",
      message,
    });
  };

  const checkOrder = (
    domain: string,
    fieldPrefix: string,
    values: number[]
  ) => {
    if (!isMonotonic(values)) {
      pushError(
        domain,
        fieldPrefix,
        "Thresholds must be strictly increasing"
      );
    }
  };

  // ===================== VOLUME =====================
  checkOrder("volume", "volume_bucket", [
    config.volume_bucket.very_low_max,
    config.volume_bucket.low_max,
    config.volume_bucket.medium_max,
    config.volume_bucket.high_max,
  ]);

  // ===================== DELTA =====================
  checkOrder("delta", "delta_bucket", [
    config.delta_bucket.delta_0_100_max,
    config.delta_bucket.delta_100_300_max,
    config.delta_bucket.delta_300_600_max,
    config.delta_bucket.delta_600_1000_max,
  ]);

  // ===================== COMPRESSION =====================
  checkOrder("compression", "compression_bucket", [
    config.compression_bucket.ultra_compressed_max,
    config.compression_bucket.compressed_max,
    config.compression_bucket.balanced_max,
    config.compression_bucket.expanded_max,
  ]);

  // ===================== ATR =====================
  checkOrder("atr", "atr_bucket", [
    config.atr_bucket.atr_0_0_5_max,
    config.atr_bucket.atr_0_5_1_0_max,
    config.atr_bucket.atr_1_0_1_5_max,
    config.atr_bucket.atr_1_5_2_5_max,
  ]);

  // ===================== PRE-BREAKOUT =====================
  checkOrder("pre_breakout", "pre_bo_bucket", [
    config.pre_bo_bucket.pre_neg_max,
    config.pre_bo_bucket.pre_0_2_max,
    config.pre_bo_bucket.pre_2_4_max,
    config.pre_bo_bucket.pre_4_6_max,
  ]);

  // ===================== TIME =====================
  checkOrder("time", "time_bucket", [
    config.time_bucket.tb_00_04_max,
    config.time_bucket.tb_04_08_max,
    config.time_bucket.tb_08_12_max,
    config.time_bucket.tb_12_16_max,
    config.time_bucket.tb_16_20_max,
    config.time_bucket.tb_20_24_max,
  ]);

  return warnings;
}

// ===================== UI HELPER (NUOVO) =====================

export function getBucketWarning(
  warnings: BucketWarning[],
  field: string
) {
  return warnings.find((w) => w.field === field);
}