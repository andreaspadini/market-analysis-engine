// packages/gui/src/features/runCreation/presets/presetStorage.ts

import type { PipelineParametersV1 } from "../state/useRunCreationState";
import type {
  PresetsState as UiPresetsState,
  RunParameters,
  RunPreset,
} from "../types";

type StoredPreset = {
  id: string;
  name: string;
  created_at: string; // ISO
  dto: PipelineParametersV1;
};

const STORAGE_KEY = "runCreation.presets.pipelineParametersV1";

/**
 * Runtime fields (or identity fields) that must NEVER appear in GUI DTO/presets.
 * We reject presets containing these keys anywhere in the object tree.
 */
const FORBIDDEN_KEYS = new Set([
  "engine_version",
  "engineVersion",
  "run_id",
  "runId",
  "config_hash",
  "configHash",
  "artifact_identity_hash",
  "artifactIdentityHash",
  "artifact_identity",
  "artifactIdentity",
  "manifest",
  "storage_path",
  "storagePath",
  "planner_state",
  "plannerState",
  "runtime_trace",
  "runtimeTrace",
]);

/** -----------------------------
 * Public API
 * ----------------------------- */

export type PresetListItem = Omit<StoredPreset, "dto">;

export function listPresets(): PresetListItem[] {
  return readAll().map(({ dto: _dto, ...meta }) => meta);
}

export function savePreset(name: string, dto: PipelineParametersV1): StoredPreset {
  const validation = validatePipelineParametersV1(dto);
  if (!validation.ok) {
    throw new Error(`Preset DTO non conforme (strict): ${validation.error}`);
  }

  const preset: StoredPreset = {
    id: cryptoLikeId(),
    name: name.trim() || "Untitled preset",
    created_at: new Date().toISOString(),
    dto: toJsonSafe(dto),
  };

  const all = readAll();
  all.unshift(preset);
  writeAll(all);
  return preset;
}

export function loadPreset(id: string): PipelineParametersV1 {
  const all = readAll();
  const preset = all.find((p) => p.id === id);
  if (!preset) throw new Error("Preset non trovato.");

  const validation = validatePipelineParametersV1(preset.dto);
  if (!validation.ok) {
    throw new Error(`Preset salvato non conforme (strict): ${validation.error}`);
  }

  return toJsonSafe(preset.dto);
}

export function deletePreset(id: string): void {
  const all = readAll();
  const next = all.filter((p) => p.id !== id);
  writeAll(next);
}

/**
 * Assertion helper: validates and narrows unknown -> PipelineParametersV1
 * Throws if DTO is not strict-conformant.
 */
function assertPipelineParametersV1(input: unknown): asserts input is PipelineParametersV1 {
  const validation = validatePipelineParametersV1(input);
  if (!validation.ok) {
    throw new Error(`Preset JSON non conforme (strict): ${validation.error}`);
  }
}

/**
 * Import raw JSON string (e.g. pasted preset) -> returns stored preset.
 * Strict: rejects non-conforming DTO.
 */
export function importPresetJson(name: string, json: string): StoredPreset {
  let parsed: unknown;

  try {
    parsed = JSON.parse(json);
  } catch {
    throw new Error("JSON non valido.");
  }

  // Strict validation + TypeScript type narrowing
  assertPipelineParametersV1(parsed);

  return savePreset(name, parsed);
}
/**
 * Export preset DTO as JSON string (snapshot).
 */
export function exportPresetJson(id: string): string {
  const dto = loadPreset(id);
  return JSON.stringify(dto, null, 2);
}

/** -----------------------------
 * Strict validation (structural)
 * ----------------------------- */

type ValidationResult = { ok: true } | { ok: false; error: string };

function validatePipelineParametersV1(input: unknown): ValidationResult {
  if (!isPlainObject(input)) return err("DTO non è un oggetto.");

  if (containsForbiddenKeys(input)) return err("DTO contiene campi runtime vietati.");

  // Top-level: api_version, dataset, engines
  const top = input as Record<string, unknown>;
  if (!hasOnlyKeys(top, ["api_version", "dataset", "engines"])) {
    return err("Top-level keys non validi (extra fields presenti o mancanti).");
  }

  const apiVersion = top.api_version;
  if (typeof apiVersion !== "string" || !apiVersion.startsWith("1.")) {
    return err("api_version non valida (atteso '1.*').");
  }

  const dataset = top.dataset;
  const engines = top.engines;

  const vd = validateDataset(dataset);
  if (!vd.ok) return vd;

  const ve = validateEngines(engines);
  if (!ve.ok) return ve;

  return ok();
}

function validateDataset(input: unknown): ValidationResult {
  if (!isPlainObject(input)) return err("dataset non è un oggetto.");
  const o = input as Record<string, unknown>;

  if (!hasOnlyKeys(o, ["instruments", "timeframe", "date_range"])) {
    return err("dataset keys non validi (extra/mancanti).");
  }

  if (!Array.isArray(o.instruments) || !o.instruments.every((x) => typeof x === "string")) {
    return err("dataset.instruments deve essere string[].");
  }

  if (typeof o.timeframe !== "string") return err("dataset.timeframe deve essere string.");

  if (!isPlainObject(o.date_range)) return err("dataset.date_range non è un oggetto.");
  const dr = o.date_range as Record<string, unknown>;
  if (!hasOnlyKeys(dr, ["start", "end"])) return err("dataset.date_range keys non validi.");
  if (typeof dr.start !== "string" || typeof dr.end !== "string") {
    return err("dataset.date_range.start/end devono essere string.");
  }

  return ok();
}

function validateEngines(input: unknown): ValidationResult {
  if (!isPlainObject(input)) return err("engines non è un oggetto.");
  const o = input as Record<string, unknown>;

  if (!hasOnlyKeys(o, ["root", "statistical", "pattern", "query"])) {
    return err("engines keys non validi (extra/mancanti).");
  }

  const vr = validateRootEngine(o.root);
  if (!vr.ok) return vr;

  const vs = validateStatisticalEngine(o.statistical);
  if (!vs.ok) return vs;

  const vp = validatePatternEngine(o.pattern);
  if (!vp.ok) return vp;

  const vq = validateQueryEngine(o.query);
  if (!vq.ok) return vq;

  return ok();
}

/**
 * Root engine validation: strict keys and nested keys as per canonical structure.
 * Types are checked structurally (string/number/boolean/object/array) without domain rules.
 */
function validateRootEngine(input: unknown): ValidationResult {
  if (!isPlainObject(input)) return err("engines.root non è un oggetto.");
  const o = input as Record<string, unknown>;

  if (
    !hasOnlyKeys(o, [
      "engine",
      "rotations",
      "duration",
      "volume",
      "delta",
      "balance",
      "breakout",
      "breakout_ranking",
      "export",
      "session_levels",
    ])
  ) {
    return err("engines.root keys non validi (extra/mancanti).");
  }

  // Minimal structural checks for required sub-objects
  const requiredObjects = [
    "engine",
    "rotations",
    "duration",
    "volume",
    "delta",
    "balance",
    "breakout",
    "breakout_ranking",
    "export",
    "session_levels",
  ] as const;

  for (const k of requiredObjects) {
    if (!isPlainObject(o[k])) return err(`engines.root.${k} non è un oggetto.`);
  }

  // We keep root validation “light” to avoid domain validation;
  // strictness here is about keys presence & forbidden extras only.
  // Subtrees are still scanned for forbidden keys globally.
  return ok();
}

function validateStatisticalEngine(input: unknown): ValidationResult {
  if (!isPlainObject(input)) return err("engines.statistical non è un oggetto.");
  const o = input as Record<string, unknown>;

  if (!hasOnlyKeys(o, ["config", "mapping", "sessions_def", "targets_def"])) {
    return err("engines.statistical keys non validi (extra/mancanti).");
  }

  if (!isPlainObject(o.config)) return err("engines.statistical.config non è un oggetto.");
  if (!isPlainObject(o.mapping)) return err("engines.statistical.mapping non è un oggetto.");
  if (!isPlainObject(o.sessions_def)) return err("engines.statistical.sessions_def non è un oggetto.");
  if (!isPlainObject(o.targets_def)) return err("engines.statistical.targets_def non è un oggetto.");

  // Keep deep validation minimal & structural only.
  // Strict extra=forbid applies to the known block boundaries (top-level & block keys).
  return ok();
}

function validatePatternEngine(input: unknown): ValidationResult {
  if (!isPlainObject(input)) return err("engines.pattern non è un oggetto.");
  const o = input as Record<string, unknown>;

  if (!hasOnlyKeys(o, ["pattern_engine", "universe", "pattern", "similarity", "outcome", "export"])) {
    return err("engines.pattern keys non validi (extra/mancanti).");
  }

  for (const k of ["pattern_engine", "universe", "pattern", "similarity", "outcome", "export"] as const) {
    if (!isPlainObject(o[k])) return err(`engines.pattern.${k} non è un oggetto.`);
  }

  return ok();
}

function validateQueryEngine(input: unknown): ValidationResult {
  if (!isPlainObject(input)) return err("engines.query non è un oggetto.");
  const o = input as Record<string, unknown>;

  if (!hasOnlyKeys(o, ["intent_id", "params"])) return err("engines.query keys non validi (extra/mancanti).");
  if (typeof o.intent_id !== "string") return err("engines.query.intent_id deve essere string.");
  if (!isPlainObject(o.params)) return err("engines.query.params deve essere oggetto.");
  return ok();
}

/** -----------------------------
 * Helpers
 * ----------------------------- */

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
  for (const k of keys) {
    if (!allowedSet.has(k)) return false;
  }
  return true;
}

function containsForbiddenKeys(input: unknown): boolean {
  const stack: unknown[] = [input];

  while (stack.length > 0) {
    const node = stack.pop();

    if (Array.isArray(node)) {
      for (const x of node) stack.push(x);
      continue;
    }

    if (!isPlainObject(node)) continue;

    for (const [k, v] of Object.entries(node)) {
      if (FORBIDDEN_KEYS.has(k)) return true;
      stack.push(v);
    }
  }

  return false;
}

/**
 * Ensures the stored DTO is JSON-serializable and immutable to callers.
 * NOTE: this is not domain validation or normalization.
 */
function toJsonSafe<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function readAll(): StoredPreset[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;

    if (!Array.isArray(parsed)) return [];
    // Lightweight storage-shape guard (do not validate dto here; validate on load)
    return parsed.filter(isStoredPresetLike) as StoredPreset[];
  } catch {
    return [];
  }
}

function writeAll(presets: StoredPreset[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(presets));
}

function isStoredPresetLike(v: unknown): v is StoredPreset {
  if (!isPlainObject(v)) return false;
  const o = v as Record<string, unknown>;
  return (
    typeof o.id === "string" &&
    typeof o.name === "string" &&
    typeof o.created_at === "string" &&
    "dto" in o
  );
}

/**
 * Simple id generator (no crypto dependency requirement).
 * If crypto.randomUUID exists, use it.
 */
function cryptoLikeId(): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const c = (globalThis as any).crypto;
  if (c?.randomUUID) return c.randomUUID();
  return `preset_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

// --- Backward-compat exports for legacy usePresets.ts ---

const LEGACY_STATE_KEY = "runCreation.presets.state.v1";

function defaultRunParameters(): RunParameters {
  return {
    dataset: null,
    window: null,
    mode: "basic",
    advanced: {},
  };
}

function toUiRunPreset(input: unknown): RunPreset | null {
  if (!isPlainObject(input)) return null;

  const o = input as Record<string, unknown>;

  if (typeof o.id !== "string") return null;
  if (typeof o.name !== "string") return null;

  const createdAt =
    typeof o.createdAt === "number"
      ? o.createdAt
      : typeof o.created_at === "string"
      ? Date.parse(o.created_at)
      : Date.now();

  const updatedAt =
    typeof o.updatedAt === "number"
      ? o.updatedAt
      : createdAt;

  const params: RunParameters =
    isPlainObject(o.params) &&
    (o.params.dataset === null || typeof o.params.dataset === "string") &&
    (o.params.window === null || typeof o.params.window === "number") &&
    (o.params.mode === "basic" || o.params.mode === "advanced") &&
    isPlainObject(o.advanced ?? o.params.advanced)
      ? {
          dataset: (o.params as Record<string, unknown>).dataset as string | null,
          window: (o.params as Record<string, unknown>).window as number | null,
          mode: (o.params as Record<string, unknown>).mode as "basic" | "advanced",
          advanced: ((o.params as Record<string, unknown>).advanced ??
            {}) as Record<string, unknown>,
        }
      : defaultRunParameters();

  return {
    id: o.id,
    name: o.name,
    createdAt: Number.isFinite(createdAt) ? createdAt : Date.now(),
    updatedAt: Number.isFinite(updatedAt) ? updatedAt : Date.now(),
    params,
  };
}

export function loadPresetsState(): UiPresetsState {
  try {
    const raw = localStorage.getItem(LEGACY_STATE_KEY);

    if (!raw) {
      return {
        presets: [],
        activePresetId: null,
      };
    }

    const parsed = JSON.parse(raw) as unknown;

    if (!isPlainObject(parsed)) {
      return {
        presets: [],
        activePresetId: null,
      };
    }

    const obj = parsed as Record<string, unknown>;
    const presets = Array.isArray(obj.presets)
      ? obj.presets
          .map((item) => toUiRunPreset(item))
          .filter((item): item is RunPreset => item !== null)
      : [];

    const activePresetId =
      typeof obj.activePresetId === "string" ? obj.activePresetId : null;

    return {
      presets,
      activePresetId,
    };
  } catch {
    return {
      presets: [],
      activePresetId: null,
    };
  }
}

export function savePresetsState(state: UiPresetsState): void {
  localStorage.setItem(LEGACY_STATE_KEY, JSON.stringify(state));
}