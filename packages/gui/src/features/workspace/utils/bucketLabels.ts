export function getBucketLabel(key: string): string {
  switch (key) {
    // Delta
    case "delta_0_100_max":
      return "Very low intensity";
    case "delta_100_300_max":
      return "Low intensity";
    case "delta_300_600_max":
      return "Medium intensity";
    case "delta_600_1000_max":
      return "High intensity";

    // Volume
    case "very_low_max":
      return "Very low volume";
    case "low_max":
      return "Low volume";
    case "medium_max":
      return "Medium volume";
    case "high_max":
      return "High volume";

    // Compression
    case "ultra_compressed_max":
      return "Ultra compressed";
    case "compressed_max":
      return "Compressed";
    case "balanced_max":
      return "Balanced";
    case "expanded_max":
      return "Expanded";

    // ATR
    case "atr_0_0_5_max":
      return "Very low volatility";
    case "atr_0_5_1_0_max":
      return "Low volatility";
    case "atr_1_0_1_5_max":
      return "Medium volatility";
    case "atr_1_5_2_5_max":
      return "High volatility";

    // Pre-breakout
    case "pre_neg_max":
      return "Negative regime";
    case "pre_0_2_max":
      return "Micro compression";
    case "pre_2_4_max":
      return "Moderate compression";
    case "pre_4_6_max":
      return "High compression";

    // Time
    case "tb_00_04_max":
      return "00–04 session";
    case "tb_04_08_max":
      return "04–08 session";
    case "tb_08_12_max":
      return "08–12 session";
    case "tb_12_16_max":
      return "12–16 session";
    case "tb_16_20_max":
      return "16–20 session";
    case "tb_20_24_max":
      return "20–24 session";

    default:
      return key;
  }
}