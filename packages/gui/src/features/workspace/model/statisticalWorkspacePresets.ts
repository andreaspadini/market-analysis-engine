type StatisticalWorkspacePresetPayload = {
  root_artifact_ref: {
    tool_id: string;
    fingerprint: string;
  };
  config: Record<string, unknown>;
};

type StatisticalWorkspacePreset = {
  id: string;
  name: string;
  created_at: string;
  payload: StatisticalWorkspacePresetPayload;
};

export type StatisticalWorkspacePresetListItem = Omit<
  StatisticalWorkspacePreset,
  "payload"
>;

const STORAGE_KEY = "workspace.statistical.presets.v1";

export function listStatisticalWorkspacePresets(): StatisticalWorkspacePresetListItem[] {
  return readAll().map(({ payload: _payload, ...meta }) => meta);
}

export function saveStatisticalWorkspacePreset(
  name: string,
  payload: StatisticalWorkspacePresetPayload
): StatisticalWorkspacePreset {
  const validation = validateStatisticalWorkspacePayload(payload);
  if (!validation.ok) {
    throw new Error(
      `Invalid statistical workspace preset payload: ${validation.error}`
    );
  }

  const preset: StatisticalWorkspacePreset = {
    id: cryptoLikeId(),
    name: name.trim() || "Untitled preset",
    created_at: new Date().toISOString(),
    payload: toJsonSafe(payload),
  };

  const all = readAll();
  all.unshift(preset);
  writeAll(all);
  return preset;
}

export function loadStatisticalWorkspacePreset(
  id: string
): StatisticalWorkspacePresetPayload {
  const all = readAll();
  const preset = all.find((p) => p.id === id);

  if (!preset) {
    throw new Error("Preset not found.");
  }

  const validation = validateStatisticalWorkspacePayload(preset.payload);
  if (!validation.ok) {
    throw new Error(`Stored preset is invalid: ${validation.error}`);
  }

  return toJsonSafe(preset.payload);
}

export function deleteStatisticalWorkspacePreset(id: string): void {
  const all = readAll();
  const next = all.filter((p) => p.id !== id);
  writeAll(next);
}

export function exportStatisticalWorkspacePresetJson(id: string): string {
  const payload = loadStatisticalWorkspacePreset(id);
  return JSON.stringify(payload, null, 2);
}

export function importStatisticalWorkspacePresetJson(
  name: string,
  json: string
): StatisticalWorkspacePreset {
  let parsed: unknown;

  try {
    parsed = JSON.parse(json);
  } catch {
    throw new Error("Invalid JSON.");
  }

  assertStatisticalWorkspacePayload(parsed);

  return saveStatisticalWorkspacePreset(name, parsed);
}

type ValidationResult = { ok: true } | { ok: false; error: string };

function validateStatisticalWorkspacePayload(input: unknown): ValidationResult {
  if (!isPlainObject(input)) {
    return err("Payload must be an object.");
  }

  const o = input as Record<string, unknown>;

  if (!hasOnlyKeys(o, ["root_artifact_ref", "config"])) {
    return err("Payload must contain only root_artifact_ref and config.");
  }

  if (!isPlainObject(o.root_artifact_ref)) {
    return err("root_artifact_ref must be an object.");
  }

  const ref = o.root_artifact_ref as Record<string, unknown>;
  if (typeof ref.tool_id !== "string" || !ref.tool_id.trim()) {
    return err("root_artifact_ref.tool_id must be a non-empty string.");
  }

  if (typeof ref.fingerprint !== "string" || !ref.fingerprint.trim()) {
    return err("root_artifact_ref.fingerprint must be a non-empty string.");
  }

  if (!isPlainObject(o.config)) {
    return err("config must be an object.");
  }

  return ok();
}

function assertStatisticalWorkspacePayload(
  input: unknown
): asserts input is StatisticalWorkspacePresetPayload {
  const validation = validateStatisticalWorkspacePayload(input);
  if (!validation.ok) {
    throw new Error(`Imported preset is invalid: ${validation.error}`);
  }
}

function ok(): ValidationResult {
  return { ok: true };
}

function err(error: string): ValidationResult {
  return { ok: false, error };
}

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function hasOnlyKeys(obj: Record<string, unknown>, allowed: string[]): boolean {
  const keys = Object.keys(obj);
  if (keys.length !== allowed.length) return false;
  const allowedSet = new Set(allowed);

  for (const key of keys) {
    if (!allowedSet.has(key)) {
      return false;
    }
  }

  return true;
}

function toJsonSafe<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function readAll(): StatisticalWorkspacePreset[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];

    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];

    return parsed.filter(isStatisticalWorkspacePresetLike) as StatisticalWorkspacePreset[];
  } catch {
    return [];
  }
}

function writeAll(presets: StatisticalWorkspacePreset[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(presets));
}

function isStatisticalWorkspacePresetLike(
  v: unknown
): v is StatisticalWorkspacePreset {
  if (!isPlainObject(v)) return false;

  const o = v as Record<string, unknown>;

  return (
    typeof o.id === "string" &&
    typeof o.name === "string" &&
    typeof o.created_at === "string" &&
    isPlainObject(o.payload)
  );
}

function cryptoLikeId(): string {
  const c = (globalThis as { crypto?: { randomUUID?: () => string } }).crypto;
  if (c?.randomUUID) {
    return c.randomUUID();
  }

  return `preset_${Date.now().toString(36)}_${Math.random()
    .toString(36)
    .slice(2, 10)}`;
}