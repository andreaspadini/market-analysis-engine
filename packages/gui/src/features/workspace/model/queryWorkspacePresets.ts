import type { QueryRunRequest } from "./workspaceTypes";

export type QueryWorkspacePreset = {
  id: string;
  name: string;
  payload: QueryRunRequest;
  created_at: string;
};

const STORAGE_KEY = "workspace.query.presets.v1";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isArtifactRef(value: unknown): boolean {
  if (!isRecord(value)) {
    return false;
  }

  return (
    typeof value.tool_id === "string" &&
    value.tool_id.trim().length > 0 &&
    typeof value.fingerprint === "string" &&
    value.fingerprint.trim().length > 0
  );
}

function isQueryPayload(value: unknown): value is QueryRunRequest {
  if (!isRecord(value)) {
    return false;
  }

  if (!isArtifactRef(value.statistical_artifact_ref)) {
    return false;
  }

  if (!isRecord(value.query)) {
    return false;
  }

  if (
    typeof value.query.intent_id !== "string" ||
    value.query.intent_id.trim().length === 0
  ) {
    return false;
  }

  if (!isRecord(value.query.params)) {
    return false;
  }

  return true;
}

function readAll(): QueryWorkspacePreset[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);

    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter((item): item is QueryWorkspacePreset => {
      return (
        isRecord(item) &&
        typeof item.id === "string" &&
        typeof item.name === "string" &&
        typeof item.created_at === "string" &&
        isQueryPayload(item.payload)
      );
    });
  } catch {
    return [];
  }
}

function writeAll(items: QueryWorkspacePreset[]): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export function listQueryWorkspacePresets(): QueryWorkspacePreset[] {
  return readAll().sort((a, b) => b.created_at.localeCompare(a.created_at));
}

export function saveQueryWorkspacePreset(
  name: string,
  payload: QueryRunRequest
): QueryWorkspacePreset {
  const normalizedName = name.trim();

  if (!normalizedName) {
    throw new Error("Preset name is required");
  }

  if (!isQueryPayload(payload)) {
    throw new Error("Invalid query preset payload");
  }

  const next: QueryWorkspacePreset = {
    id: crypto.randomUUID(),
    name: normalizedName,
    payload,
    created_at: new Date().toISOString(),
  };

  const items = readAll();
  items.push(next);
  writeAll(items);

  return next;
}

export function loadQueryWorkspacePreset(
  id: string
): QueryWorkspacePreset | null {
  return readAll().find((item) => item.id === id) ?? null;
}

export function deleteQueryWorkspacePreset(id: string): void {
  const next = readAll().filter((item) => item.id !== id);
  writeAll(next);
}

export function exportQueryWorkspacePresetJson(id: string): string {
  const preset = loadQueryWorkspacePreset(id);

  if (!preset) {
    throw new Error("Preset not found");
  }

  return JSON.stringify(preset.payload, null, 2);
}

export function importQueryWorkspacePresetJson(
  name: string,
  json: string
): QueryWorkspacePreset {
  const normalizedName = name.trim();

  if (!normalizedName) {
    throw new Error("Preset name is required");
  }

  let parsed: unknown;

  try {
    parsed = JSON.parse(json);
  } catch {
    throw new Error("Invalid preset JSON");
  }

  if (!isQueryPayload(parsed)) {
    throw new Error("Preset JSON must match the query payload shape");
  }

  return saveQueryWorkspacePreset(normalizedName, parsed);
}