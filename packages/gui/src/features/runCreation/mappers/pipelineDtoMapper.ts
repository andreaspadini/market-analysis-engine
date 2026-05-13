// packages/gui/src/features/runCreation/mappers/pipelineDtoMapper.ts

import type {
  PipelineParametersV1,
  RunCreationState,
} from "../state/useRunCreationState";

/**
 * G2.3 / A2 — DTO Mapper (Deterministic, 1:1)
 *
 * Contract rules (vincolanti):
 * - Mapping 1:1 tra state e DTO
 * - No rename / no normalization / no planner rules / no hash
 * - No runtime fields (engine_version/run_id/config_hash/artifact_identity_hash/manifest/storage_path/...)
 *
 * NOTE:
 * - This mapper is intentionally "dumb": it only converts state -> JSON-safe DTO and back.
 * - Strict validation is performed by O6 (and preset strict checks in A3).
 */

/**
 * Ensures the output is JSON-serializable and immune to accidental mutation.
 * - Removes undefined (JSON would drop it anyway)
 * - Keeps null
 * - Keeps arrays/objects shape
 *
 * This is NOT domain validation nor schema generation.
 */
function toJsonSafe<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export function toPipelineParametersV1(
  state: Pick<RunCreationState, "pipelineParametersV1">
): PipelineParametersV1 {
  // Deterministic: no transformation other than JSON-safety clone.
  return toJsonSafe(state.pipelineParametersV1);
}

export function fromPipelineParametersV1(dto: PipelineParametersV1): PipelineParametersV1 {
  // Symmetric load: do not mutate / do not "fix".
  return toJsonSafe(dto);
}