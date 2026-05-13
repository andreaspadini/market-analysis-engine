export type RootEvent = Record<string, unknown>;

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isPrimitive(value: unknown) {
  return (
    value === null ||
    value === undefined ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  );
}

export function formatLabel(key: string) {
  return key
    .replace(/_/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function formatValue(value: unknown) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "—";
  if (typeof value === "string") return value || "—";
  return "—";
}

export function compactPreview(value: unknown) {
  if (value === null || value === undefined) return "null";
  if (Array.isArray(value)) return `Array(${value.length})`;
  if (isRecord(value)) return `Object(${Object.keys(value).length})`;
  return String(value);
}

export function getStringField(event: RootEvent, ...keys: string[]) {
  for (const key of keys) {
    const value = event[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return "—";
}

export function getNumberField(event: RootEvent, ...keys: string[]) {
  for (const key of keys) {
    const value = event[key];
    if (typeof value === "number") return value;
  }
  return null;
}