import type { HttpClient } from "../client/httpClient";
import type { PipelineParametersV1 } from "../../features/runCreation/state/useRunCreationState";

export type O6ApiVersion = "1.0";

/* ============================================================
   Run Status
============================================================ */

export type O6RunStatus =
  | "PENDING"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED";

/* ============================================================
   Canonical Stepwise Types
============================================================ */

export type O6ArtifactRef = {
  tool_id: string;
  fingerprint: string;
};

export type O6PostRootRunRequest = {
  api_version: O6ApiVersion;
  dataset: Record<string, unknown>;
  config: Record<string, unknown>;
};

export type O6PostRootRunResponse = {
  api_version: O6ApiVersion;
  run_id: string;
  fingerprint?: string;
  status?: O6RunStatus;
  artifact?: O6ArtifactRef;
};

export type O6PostStatisticalRunRequest = {
  api_version: O6ApiVersion;
  root_artifact_ref: O6ArtifactRef;
  config: Record<string, unknown>;
};

export type O6PostStatisticalRunResponse = {
  api_version: O6ApiVersion;
  run_id: string;
  fingerprint?: string;
  status?: O6RunStatus;
  artifact?: O6ArtifactRef;
};

export type O6PostQueryRunRequest = {
  api_version: O6ApiVersion;
  statistical_artifact_ref: O6ArtifactRef;
  intent_id: string;
  params: Record<string, unknown>;
};

export type O6PostQueryRunResponse = {
  api_version: O6ApiVersion;
  run_id: string;
  fingerprint?: string;
  status?: O6RunStatus;
  artifact?: O6ArtifactRef;
};

export type O6PostPatternRunRequest = {
  api_version: O6ApiVersion;
  dataset: Record<string, unknown>;
  config: Record<string, unknown>;
};

export type O6PostPatternRunResponse = {
  api_version: O6ApiVersion;
  run_id: string;
  fingerprint?: string;
  status?: O6RunStatus;
  artifact?: O6ArtifactRef;
};

export type O6ArtifactManifestOutput = {
  relpath: string;
  bytes?: number;
  checksum?: {
    alg: string;
    value: string;
  };
};

export type O6ArtifactManifestResponse = {
  manifest_version: string;
  outputs: O6ArtifactManifestOutput[];
  producer?: {
    tool_id: string;
    tool_version?: string;
  };
  lineage?: Record<string, unknown>;
};

export type O6QueryPublicIntentCatalogEntry = {
  intent_id: string;
  params_schema?: Record<string, unknown>;
  deprecated?: boolean;
  replacement_intent_id?: string | null;
  semantic_note?: string | null;
  example_description?: string | null;
  example_params?: Record<string, unknown> | null;
};

export type O6QueryPublicIntentCatalogResponse = {
  api_version: O6ApiVersion;
  items: O6QueryPublicIntentCatalogEntry[];
};

/* ============================================================
   Submit Run (Legacy bridge)
============================================================ */

export type O6SubmitRunRequest = {
  api_version: O6ApiVersion;
  config: {
    config_version: "1.0";
    pipeline: { id: string };

    /**
     * G2.3: strict DTO (PipelineParametersV1) deve essere inviato completo.
     *
     * Non-breaking:
     * - mantiene compatibilità con chiamanti legacy che passavano Record<string, unknown>
     * - i nuovi chiamanti devono passare PipelineParametersV1 (strict-validabile da O6)
     */
    parameters: PipelineParametersV1 | Record<string, unknown>;
  };
};

export type O6SubmitRunResponse = {
  api_version: O6ApiVersion;
  run_id: string;
  fingerprint: string;
  status: O6RunStatus;
};

/* ============================================================
   Get Run (G3.1)
============================================================ */

export type O6GetRunResponse = {
  api_version: O6ApiVersion;
  run_id: string;
  fingerprint: string;
  status: O6RunStatus;
};

/* ============================================================
   Get Run Results (G3.2)
============================================================ */

export type O6GetRunResultsResponse = {
  api_version: O6ApiVersion;
  run_id: string;
  results: Record<string, unknown>;
};

/* ============================================================
   Error Body (Engine contract)
============================================================ */

export type O6ErrorBody = {
  api_version: O6ApiVersion;
  error_code:
    | "INVALID_REQUEST"
    | "INVALID_CONFIG"
    | "INVALID_VERSION"
    | "NOT_FOUND"
    | "INTERNAL_ERROR"
    | "INVALID_INTENT"
    | "INVALID_ARTIFACT_REF";
  message: string;
  details?: Record<string, unknown>;
};


/* ============================================================
   Client Interface
============================================================ */

export type O6Client = {
  postRootRun(request: O6PostRootRunRequest): Promise<O6PostRootRunResponse>;

  postStatisticalRun(
    request: O6PostStatisticalRunRequest
  ): Promise<O6PostStatisticalRunResponse>;

  postQueryRun(
    request: O6PostQueryRunRequest
  ): Promise<O6PostQueryRunResponse>;

  postPatternRun(
    request: O6PostPatternRunRequest
  ): Promise<O6PostPatternRunResponse>;

  submitRun(request: O6SubmitRunRequest): Promise<O6SubmitRunResponse>;

  getRun(runId: string): Promise<O6GetRunResponse>;

  getRunResults(runId: string): Promise<O6GetRunResultsResponse>;

  getArtifactManifest(
    toolId: string,
    fingerprint: string
  ): Promise<O6ArtifactManifestResponse>;

  getArtifactJson<T = unknown>(
    toolId: string,
    fingerprint: string,
    relpath: string
  ): Promise<T>;

  getQueryPublicIntentCatalog(): Promise<O6QueryPublicIntentCatalogResponse>;

}

  

/* ============================================================
   Factory (Injection-based, no singleton)
============================================================ */

export function createO6Client(http: HttpClient): O6Client {
  return {
    postRootRun(request) {
      return http.post<O6PostRootRunResponse>("/runs/root", request);
    },

    postStatisticalRun(request) {
      return http.post<O6PostStatisticalRunResponse>(
        "/runs/statistical",
        request
      );
    },

    postQueryRun(request) {
      return http.post<O6PostQueryRunResponse>("/runs/query", request);
    },

    postPatternRun(request) {
      return http.post<O6PostPatternRunResponse>("/runs/pattern", request);
    },

    submitRun(request) {
      return http.post<O6SubmitRunResponse>("/runs", request);
    },

    getRun(runId: string) {
      return http.get<O6GetRunResponse>(
        `/runs/${encodeURIComponent(runId)}`
      );
    },

    getRunResults(runId: string) {
      return http.get<O6GetRunResultsResponse>(
        `/runs/${encodeURIComponent(runId)}/results`
      );
    },

    getArtifactManifest(toolId: string, fingerprint: string) {
      return http.get<O6ArtifactManifestResponse>(
        `/manifests/${encodeURIComponent(toolId)}/${encodeURIComponent(
          fingerprint
        )}`
      );
    },

    getArtifactJson<T = unknown>(
      toolId: string,
      fingerprint: string,
      relpath: string
    ) {
      return http.get<T>(
        `/artifacts/${encodeURIComponent(toolId)}/${encodeURIComponent(
          fingerprint
        )}/${relpath}`
      );
    },

    getQueryPublicIntentCatalog() {
      return http.get<O6QueryPublicIntentCatalogResponse>(
        "/query/public-intents"
      );
    },
  };
}