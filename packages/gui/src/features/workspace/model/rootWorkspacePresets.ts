type RootWorkspacePresetPayload = {
  dataset: Record<string, unknown>;
  config: Record<string, unknown>;
};

type RootWorkspacePreset = {
  id: string;
  name: string;
  created_at: string;
  payload: RootWorkspacePresetPayload;
};

export type RootWorkspacePresetListItem = Omit<RootWorkspacePreset, "payload">;

const STORAGE_KEY = "workspace.root.presets.v1";

export function listRootWorkspacePresets(): RootWorkspacePresetListItem[] {
  return readAll().map(({ payload: _payload, ...meta }) => meta);
}

export function saveRootWorkspacePreset(
  name: string,
  payload: RootWorkspacePresetPayload
): RootWorkspacePreset {
  const validation = validateRootWorkspacePayload(payload);
  if (!validation.ok) {
    throw new Error(`Invalid root workspace preset payload: ${validation.error}`);
  }

  const preset: RootWorkspacePreset = {
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

export function loadRootWorkspacePreset(
  id: string
): RootWorkspacePresetPayload {
  const all = readAll();
  const preset = all.find((p) => p.id === id);

  if (!preset) {
    throw new Error("Preset not found.");
  }

  const validation = validateRootWorkspacePayload(preset.payload);
  if (!validation.ok) {
    throw new Error(`Stored preset is invalid: ${validation.error}`);
  }

  return toJsonSafe(preset.payload);
}

export function deleteRootWorkspacePreset(id: string): void {
  const all = readAll();
  const next = all.filter((p) => p.id !== id);
  writeAll(next);
}

export function exportRootWorkspacePresetJson(id: string): string {
  const payload = loadRootWorkspacePreset(id);
  return JSON.stringify(payload, null, 2);
}

export function importRootWorkspacePresetJson(
  name: string,
  json: string
): RootWorkspacePreset {
  let parsed: unknown;

  try {
    parsed = JSON.parse(json);
  } catch {
    throw new Error("Invalid JSON.");
  }

  assertRootWorkspacePayload(parsed);

  return saveRootWorkspacePreset(name, parsed);
}

type ValidationResult = { ok: true } | { ok: false; error: string };

function validateRootWorkspacePayload(input: unknown): ValidationResult {
  if (!isPlainObject(input)) {
    return err("Payload must be an object.");
  }

  const o = input as Record<string, unknown>;

  if (!hasOnlyKeys(o, ["dataset", "config"])) {
    return err("Payload must contain only dataset and config.");
  }

  if (!isPlainObject(o.dataset)) {
    return err("dataset must be an object.");
  }

  if (!isPlainObject(o.config)) {
    return err("config must be an object.");
  }

  return ok();
}

function assertRootWorkspacePayload(
  input: unknown
): asserts input is RootWorkspacePresetPayload {
  const validation = validateRootWorkspacePayload(input);
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

function readAll(): RootWorkspacePreset[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];

    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];

    return parsed.filter(isRootWorkspacePresetLike) as RootWorkspacePreset[];
  } catch {
    return [];
  }
}

function writeAll(presets: RootWorkspacePreset[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(presets));
}

function isRootWorkspacePresetLike(v: unknown): v is RootWorkspacePreset {
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