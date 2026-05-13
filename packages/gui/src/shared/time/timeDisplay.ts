export type TimeDisplayMode = "utc" | "local";

function normalizeTimestampInput(value: unknown): string | null {
  if (typeof value !== "string") return null;

  const trimmed = value.trim();
  if (!trimmed) return null;

  return trimmed;
}

export function parseTimestampAsUtcDate(value: unknown): Date | null {
  const normalized = normalizeTimestampInput(value);
  if (!normalized) return null;

  const withZone = /[zZ]|[+-]\d{2}:\d{2}$/.test(normalized)
    ? normalized
    : `${normalized}Z`;

  const date = new Date(withZone);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function toChartUnixSeconds(value: unknown): number | null {
  const date = parseTimestampAsUtcDate(value);
  if (!date) return null;
  return Math.floor(date.getTime() / 1000);
}

export function formatTimestamp(
  value: unknown,
  mode: TimeDisplayMode,
  options?: Intl.DateTimeFormatOptions
): string {
  const date = parseTimestampAsUtcDate(value);
  if (!date) return "—";

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: mode === "utc" ? "UTC" : undefined,
    ...options,
  }).format(date);
}