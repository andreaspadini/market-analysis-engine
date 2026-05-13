import React from "react";
import { useApi } from "../../../api/ApiProvider";
import { createWorkspaceClient } from "../api/workspaceClient";
import type { QueryWorkspaceState } from "../model/queryWorkspaceState";
import type {
  ArtifactRefInput,
  QueryRunRequest,
} from "../model/workspaceTypes";
import { ArtifactRefBadge } from "./ArtifactRefBadge";
import { StepStatusBanner } from "./StepStatusBanner";
import { ArtifactSelector } from "./ArtifactSelector";
import {
  getQueryIntentCatalogEntry,
  normalizeQueryIntentCatalog,
  type QueryIntentCatalogEntry,
} from "../model/queryIntentCatalog";
import {
  deleteQueryWorkspacePreset,
  exportQueryWorkspacePresetJson,
  importQueryWorkspacePresetJson,
  listQueryWorkspacePresets,
  loadQueryWorkspacePreset,
  saveQueryWorkspacePreset,
} from "../model/queryWorkspacePresets";
import { QueryResultsSection } from "../../runresults/sections/QueryResultsSection";

type QueryWorkspaceCardProps = {
  availableStatisticalArtifacts?: ArtifactRefInput[];
  initialStatisticalArtifactRef?: ArtifactRefInput | null;
  onArtifactProduced?: (artifactRef: ArtifactRefInput | null) => void;
};

type ArtifactManifestOutput = {
  relpath: string;
};

type ArtifactManifest = {
  outputs?: ArtifactManifestOutput[];
};

export function QueryWorkspaceCard(props: QueryWorkspaceCardProps) {
  const {
    availableStatisticalArtifacts = [],
    initialStatisticalArtifactRef = null,
    onArtifactProduced,
  } = props;
  const { o6 } = useApi();
  const workspaceClient = React.useMemo(() => createWorkspaceClient(o6), [o6]);
  const [queryIntentCatalog, setQueryIntentCatalog] = React.useState<
    QueryIntentCatalogEntry[]
  >([]);
  const [queryIntentCatalogLoading, setQueryIntentCatalogLoading] =
    React.useState<boolean>(false);
  const [queryIntentCatalogError, setQueryIntentCatalogError] =
    React.useState<string | null>(null);

  const [statisticalArtifactInput, setStatisticalArtifactInput] =
    React.useState<ArtifactRefInput>({
      tool_id: initialStatisticalArtifactRef?.tool_id ?? "",
      fingerprint: initialStatisticalArtifactRef?.fingerprint ?? "",
    });

  const [intentId, setIntentId] = React.useState<string>("true_breakout_rate");
  const [selectedCatalogIntentId, setSelectedCatalogIntentId] =
    React.useState<string>("");
  const [paramsText, setParamsText] = React.useState<string>(
    JSON.stringify(
      {
        group_by: ["session"],
      },
      null,
      2
    )
  );
  const [paramsError, setParamsError] = React.useState<string | null>(null);
  const [presetName, setPresetName] = React.useState<string>("");
  const [selectedPresetId, setSelectedPresetId] = React.useState<string>("");
  const [presetStatus, setPresetStatus] = React.useState<string | null>(null);
  const [importName, setImportName] = React.useState<string>("");
  const [importJson, setImportJson] = React.useState<string>("");
  const [exportJson, setExportJson] = React.useState<string>("");
  const [availablePresets, setAvailablePresets] = React.useState(
    listQueryWorkspacePresets()
  );
  const [isPresetOpen, setIsPresetOpen] = React.useState<boolean>(false);

  const [resultsData, setResultsData] = React.useState<unknown>(null);
  const [resultsLoading, setResultsLoading] = React.useState<boolean>(false);
  const [resultsError, setResultsError] = React.useState<string | null>(null);

  const [state, setState] = React.useState<QueryWorkspaceState>({
    loading: false,
    error: null,
    lastRunId: null,
    selectedStatisticalArtifactRef: initialStatisticalArtifactRef,
    artifactRef: null,
    status: "IDLE",
  });

  const selectedIntentEntry = React.useMemo(() => {
    if (selectedCatalogIntentId) {
      return getQueryIntentCatalogEntry(queryIntentCatalog, selectedCatalogIntentId);
    }

    return getQueryIntentCatalogEntry(queryIntentCatalog, intentId);
  }, [queryIntentCatalog, selectedCatalogIntentId, intentId]);

  const parsedParams = React.useMemo(() => safeParse(paramsText), [paramsText]);

  React.useEffect(() => {
    let isActive = true;

    async function loadQueryIntentCatalog() {
      setQueryIntentCatalogLoading(true);
      setQueryIntentCatalogError(null);

      try {
        const response = await workspaceClient.getQueryPublicIntentCatalog();
        const items = Array.isArray(response.items) ? response.items : [];
        const normalized = normalizeQueryIntentCatalog(items);

        if (!isActive) return;

        setQueryIntentCatalog(normalized);
      } catch {
        if (!isActive) return;

        setQueryIntentCatalog([]);
        setQueryIntentCatalogError("Failed to load query public intent catalog");
      } finally {
        if (isActive) {
          setQueryIntentCatalogLoading(false);
        }
      }
    }

    loadQueryIntentCatalog();

    return () => {
      isActive = false;
    };
  }, [workspaceClient]);

  React.useEffect(() => {
    if (!initialStatisticalArtifactRef) {
      return;
    }

    setStatisticalArtifactInput(initialStatisticalArtifactRef);
    setState((s) => ({
      ...s,
      selectedStatisticalArtifactRef: initialStatisticalArtifactRef,
    }));
  }, [initialStatisticalArtifactRef]);

  function safeParse(json: string): Record<string, unknown> | null {
    try {
      const parsed = JSON.parse(json);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>;
      }
      return null;
    } catch {
      return null;
    }
  }

  function validateArtifactRef(value: ArtifactRefInput): ArtifactRefInput | null {
    const tool_id = value.tool_id.trim();
    const fingerprint = value.fingerprint.trim();

    if (!tool_id || !fingerprint) {
      return null;
    }

    return { tool_id, fingerprint };
  }

  function refreshPresets() {
    setAvailablePresets(listQueryWorkspacePresets());
  }

  function buildQueryObject(): QueryRunRequest["query"] {
    return {
      intent_id: intentId.trim(),
      params: parsedParams ?? {},
    };
  }

  function buildPreviewPayload(): QueryRunRequest {
    return {
      statistical_artifact_ref: {
        tool_id: statisticalArtifactInput.tool_id.trim(),
        fingerprint: statisticalArtifactInput.fingerprint.trim(),
      },
      query: buildQueryObject(),
    };
  }

  function buildCurrentPayload(): QueryRunRequest {
    const statistical_artifact_ref = validateArtifactRef(statisticalArtifactInput);
    const query = buildQueryObject();

    if (!statistical_artifact_ref) {
      throw new Error("Statistical artifact reference is required");
    }

    if (!query.intent_id) {
      throw new Error("Intent ID is required");
    }

    if (!parsedParams) {
      throw new Error("Invalid JSON in params");
    }

    return {
      statistical_artifact_ref,
      query,
    };
  }

  function applyPayloadToForm(payload: QueryRunRequest) {
    setStatisticalArtifactInput(payload.statistical_artifact_ref);
    setState((s) => ({
      ...s,
      selectedStatisticalArtifactRef: payload.statistical_artifact_ref,
    }));

    setIntentId(payload.query.intent_id);

    const matched = getQueryIntentCatalogEntry(
      queryIntentCatalog,
      payload.query.intent_id
    );
    setSelectedCatalogIntentId(matched?.intentId ?? "");

    setParamsText(JSON.stringify(payload.query.params, null, 2));
    setParamsError(null);

    setResultsData(null);
    setResultsError(null);
  }

  function handleApplyExampleParams() {
    if (!selectedIntentEntry) {
      return;
    }

    setParamsText(JSON.stringify(selectedIntentEntry.exampleParams, null, 2));
  }

  function handleFormatParams() {
    const parsed = safeParse(paramsText);

    if (!parsed) {
      setParamsError("Params must be a valid JSON object");
      return;
    }

    setParamsText(JSON.stringify(parsed, null, 2));
    setParamsError(null);
  }

  function handleResetParams() {
    setParamsText(
      JSON.stringify(
        {
          group_by: ["session"],
        },
        null,
        2
      )
    );
    setParamsError(null);
  }

  async function handleSubmit() {
    let payload: QueryRunRequest;

    try {
      payload = buildCurrentPayload();
    } catch (error: unknown) {
      const message =
        error instanceof Error && error.message
          ? error.message
          : "Invalid query payload";

      setState((s) => ({
        ...s,
        error: message,
      }));
      return;
    }

    setResultsData(null);
    setResultsError(null);

    setState({
      loading: true,
      error: null,
      lastRunId: null,
      selectedStatisticalArtifactRef: payload.statistical_artifact_ref,
      artifactRef: null,
      status: "PENDING",
    });

    try {
      const response = await workspaceClient.postQueryRun(payload);

      setState((s) => ({
        ...s,
        loading: true,
        lastRunId: response.run_id,
        artifactRef: response.artifact,
        status: "PENDING",
      }));
      onArtifactProduced?.(response.artifact);
    } catch (error: unknown) {
      let message = "Failed to submit query run";

      if (error instanceof Error && error.message) {
        message = error.message;
      } else if (
        typeof error === "object" &&
        error !== null &&
        "message" in error &&
        typeof (error as { message?: unknown }).message === "string"
      ) {
        message = (error as { message: string }).message;
      }

      setState((s) => ({
        ...s,
        loading: false,
        error: message,
        status: "FAILED",
      }));
    }
  }

  function handleSavePreset() {
    try {
      const payload = buildCurrentPayload();
      saveQueryWorkspacePreset(presetName, payload);
      refreshPresets();
      setPresetStatus("Preset saved");
      setPresetName("");
    } catch (error: unknown) {
      const message =
        error instanceof Error && error.message
          ? error.message
          : "Failed to save preset";

      setPresetStatus(message);
    }
  }

  function handleLoadPreset() {
    if (!selectedPresetId) {
      setPresetStatus("Select a preset to load");
      return;
    }

    const preset = loadQueryWorkspacePreset(selectedPresetId);

    if (!preset) {
      setPresetStatus("Preset not found");
      refreshPresets();
      return;
    }

    applyPayloadToForm(preset.payload);
    setPresetStatus("Preset loaded");
  }

  function handleDeletePreset() {
    if (!selectedPresetId) {
      setPresetStatus("Select a preset to delete");
      return;
    }

    deleteQueryWorkspacePreset(selectedPresetId);
    refreshPresets();
    setSelectedPresetId("");
    setExportJson("");
    setPresetStatus("Preset deleted");
  }

  function handleExportPreset() {
    if (!selectedPresetId) {
      setPresetStatus("Select a preset to export");
      return;
    }

    try {
      const json = exportQueryWorkspacePresetJson(selectedPresetId);
      setExportJson(json);
      setPresetStatus("Preset exported");
    } catch (error: unknown) {
      const message =
        error instanceof Error && error.message
          ? error.message
          : "Failed to export preset";

      setPresetStatus(message);
    }
  }

  function handleImportPreset() {
    try {
      importQueryWorkspacePresetJson(importName, importJson);
      refreshPresets();
      setPresetStatus("Preset imported");
      setImportName("");
      setImportJson("");
    } catch (error: unknown) {
      const message =
        error instanceof Error && error.message
          ? error.message
          : "Failed to import preset";

      setPresetStatus(message);
    }
  }

  React.useEffect(() => {
    if (!paramsText.trim()) {
      setParamsError("Params must be a valid JSON object");
      return;
    }

    if (!parsedParams) {
      setParamsError("Params must be a valid JSON object");
      return;
    }

    setParamsError(null);
  }, [paramsText, parsedParams]);

  React.useEffect(() => {
    if (!state.lastRunId) return;

    let isActive = true;

    const interval = window.setInterval(async () => {
      try {
        const run = await o6.getRun(state.lastRunId as string);

        if (!isActive) return;

        const status = run.status;

        if (status === "PENDING" || status === "RUNNING") {
          setState((s) => ({
            ...s,
            status,
            loading: true,
          }));
          return;
        }

        if (status === "SUCCEEDED") {
          setState((s) => ({
            ...s,
            status: "SUCCEEDED",
            loading: false,
          }));
          window.clearInterval(interval);
          return;
        }

        if (status === "FAILED") {
          setState((s) => ({
            ...s,
            status: "FAILED",
            loading: false,
          }));
          window.clearInterval(interval);
        }
      } catch {
        if (!isActive) return;

        setState((s) => ({
          ...s,
          status: "NOT_FOUND",
          loading: false,
        }));

        window.clearInterval(interval);
      }
    }, 2500);

    return () => {
      isActive = false;
      window.clearInterval(interval);
    };
  }, [state.lastRunId, o6]);

  React.useEffect(() => {
    if (state.status !== "SUCCEEDED" || !state.artifactRef) {
      return;
    }

    const artifactRef = state.artifactRef;
    let isActive = true;

    async function loadResults() {
      setResultsLoading(true);
      setResultsError(null);

      try {
        const manifest = await workspaceClient.getArtifactManifest(
          artifactRef.tool_id,
          artifactRef.fingerprint
        );

        if (!isActive) {
          return;
        }

        const m = manifest as {
          manifest?: {
            outputs?: Array<{ relpath?: string }>;
          };
        };

        const rawOutputs = m.manifest?.outputs;

        const outputs = Array.isArray(rawOutputs) ? rawOutputs : [];

        const reportRelpath = outputs.find(
          (o) => typeof o.relpath === "string" && o.relpath.endsWith("report.json")
        )?.relpath;

        const insightRelpath = outputs.find(
          (o) => typeof o.relpath === "string" && o.relpath.endsWith("insight.json")
        )?.relpath;

        let report: unknown = null;
        let insight: unknown = null;

        if (reportRelpath) {
          report = await workspaceClient.getArtifactJson(
            artifactRef.tool_id,
            artifactRef.fingerprint,
            reportRelpath
          );
        }

        if (insightRelpath) {
          insight = await workspaceClient.getArtifactJson(
            artifactRef.tool_id,
            artifactRef.fingerprint,
            insightRelpath
          );
        }

        if (!isActive) {
          return;
        }

        setResultsData({ report, insight });
      } catch (error: unknown) {
        if (!isActive) {
          return;
        }

        const message =
          error instanceof Error && error.message
            ? error.message
            : "Failed to load query results";

        setResultsError(message);
        setResultsData(null);
      } finally {
        if (isActive) {
          setResultsLoading(false);
        }
      }
    }

    loadResults();

    return () => {
      isActive = false;
    };
  }, [state.status, state.artifactRef, workspaceClient]);

  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: 14, padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Query Stage</h2>

      <div className="subtle" style={{ marginBottom: 16 }}>
        Build a reusable question over a Statistical artifact and inspect the result directly.
      </div>

      {/* ================= TOP CONTROL PLANE ================= */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) 320px",
          gap: 16,
          alignItems: "stretch",
          marginBottom: 20,
        }}
      >
        {/* LEFT: STATISTICAL ARTIFACT */}
        <div
          style={{
            border: "1px solid var(--border)",
            borderRadius: 14,
            padding: 14,
            background: "var(--surface)",
          }}
        >
          <div style={{ marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ fontWeight: 900, fontSize: 15 }}>Statistical Artifact</div>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 800,
                  letterSpacing: 0.8,
                  opacity: 0.65,
                  border: "1px solid var(--border)",
                  borderRadius: 999,
                  padding: "2px 7px",
                }}
              >
                INPUT
              </span>
            </div>

            <div className="subtle" style={{ marginTop: 4, fontSize: "var(--font-sm)" }}>
              Select the Statistical output queried by this stage.
            </div>
          </div>

          <ArtifactSelector
            available={availableStatisticalArtifacts}
            selected={state.selectedStatisticalArtifactRef}
            onSelect={(ref) => {
              setStatisticalArtifactInput(ref);
              setState((s) => ({
                ...s,
                selectedStatisticalArtifactRef: ref,
              }));
              setResultsData(null);
              setResultsError(null);
            }}
            onManualChange={(ref) => {
              setStatisticalArtifactInput(ref ?? { tool_id: "", fingerprint: "" });
              setState((s) => ({
                ...s,
                selectedStatisticalArtifactRef: ref,
              }));
              setResultsData(null);
              setResultsError(null);
            }}
          />
        </div>

        {/* RIGHT: SAVED QUERIES */}
        <div
          style={{
            border: "1px solid var(--border)",
            borderRadius: 14,
            padding: 14,
            background: "var(--surface)",
          }}
        >
          <div style={{ marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ fontWeight: 900, fontSize: 15 }}>Saved Queries</div>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 800,
                  letterSpacing: 0.8,
                  opacity: 0.65,
                  border: "1px solid var(--border)",
                  borderRadius: 999,
                  padding: "2px 7px",
                }}
              >
                UTILITY
              </span>
            </div>

            <div className="subtle" style={{ marginTop: 4, fontSize: "var(--font-sm)" }}>
              Save and reuse intent + params.
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {presetStatus ? <div className="pill">{presetStatus}</div> : null}

            <div>
              <label>Query name</label>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  type="text"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  placeholder="Query name"
                  style={{ minWidth: 0, flex: 1 }}
                />
                <button type="button" onClick={handleSavePreset}>
                  Save
                </button>
              </div>
            </div>

            <div>
              <label>Saved query</label>
              <select
                value={selectedPresetId}
                onChange={(e) => setSelectedPresetId(e.target.value)}
                style={{ width: "100%" }}
              >
                <option value="">Select query</option>
                {availablePresets.map((preset) => (
                  <option key={preset.id} value={preset.id}>
                    {preset.name}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
              <button type="button" onClick={handleLoadPreset} disabled={!selectedPresetId}>
                Load
              </button>
              <button type="button" onClick={handleDeletePreset} disabled={!selectedPresetId}>
                Delete
              </button>
              <button type="button" onClick={handleExportPreset} disabled={!selectedPresetId}>
                Export
              </button>
            </div>

            <details>
              <summary style={{ cursor: "pointer", fontSize: 12, opacity: 0.75 }}>
                Advanced import / export
              </summary>

              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
                <input
                  type="text"
                  value={importName}
                  onChange={(e) => setImportName(e.target.value)}
                  placeholder="Imported query name"
                />

                <textarea
                  value={importJson}
                  onChange={(e) => setImportJson(e.target.value)}
                  rows={3}
                  style={{ width: "100%", fontFamily: "monospace", fontSize: 11 }}
                  placeholder="Paste query preset JSON"
                />

                <button type="button" onClick={handleImportPreset} disabled={!importJson.trim()}>
                  Import
                </button>

                {exportJson ? (
                  <textarea
                    value={exportJson}
                    readOnly
                    rows={3}
                    style={{ width: "100%", fontFamily: "monospace", fontSize: 11 }}
                  />
                ) : null}
              </div>
            </details>
          </div>
        </div>
      </div>

      {/* ================= QUERY BUILDER ================= */}
      <div
        style={{
          border: "1px solid var(--border)",
          borderRadius: 14,
          padding: 14,
          background: "var(--surface)",
          marginBottom: 12,
        }}
      >
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ fontWeight: 900, fontSize: 15 }}>Query Intent</div>
            <span className="pill">CORE</span>
          </div>
          <div className="subtle" style={{ marginTop: 4 }}>
            Choose the question to ask over the selected statistical dataset.
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <label>Known public intents</label>

          {queryIntentCatalogLoading ? (
            <div className="subtle" style={{ marginTop: 6 }}>
              Loading backend public intent catalog...
            </div>
          ) : null}

          {queryIntentCatalogError ? (
            <div style={{ fontSize: 12, color: "#b45309", marginTop: 6 }}>
              {queryIntentCatalogError}
            </div>
          ) : null}

          <select
            value={selectedCatalogIntentId}
            onChange={(e) => {
              const nextIntentId = e.target.value;
              setSelectedCatalogIntentId(nextIntentId);

              if (nextIntentId) {
                setIntentId(nextIntentId);
              }

              setResultsData(null);
              setResultsError(null);
            }}
            style={{ width: "100%" }}
          >
            <option value="">Select a known public intent</option>
            {queryIntentCatalog.map((entry) => (
              <option key={entry.intentId} value={entry.intentId}>
                {entry.label} ({entry.intentId})
              </option>
            ))}
          </select>
        </div>

        {selectedIntentEntry ? (
          <div
            style={{
              marginBottom: 12,
              padding: 10,
              border: "1px solid var(--border)",
              borderRadius: 10,
              background: "rgba(255,255,255,0.03)",
            }}
          >
            <div style={{ marginBottom: 4 }}>
              <strong>{selectedIntentEntry.label}</strong>
            </div>

            <div className="subtle" style={{ marginBottom: 8 }}>
              {selectedIntentEntry.description}
            </div>

            <button type="button" onClick={handleApplyExampleParams}>
              Load example params
            </button>
          </div>
        ) : null}

        <div>
          <label>Intent ID</label>
          <input
            type="text"
            value={intentId}
            onChange={(e) => {
              const nextValue = e.target.value;
              setIntentId(nextValue);

              const matched = getQueryIntentCatalogEntry(queryIntentCatalog, nextValue);
              setSelectedCatalogIntentId(matched?.intentId ?? "");

              setResultsData(null);
              setResultsError(null);
            }}
            placeholder="Enter a public intent ID or select one above"
            style={{ width: "100%" }}
          />

          <div className="subtle" style={{ marginTop: 6 }}>
            The intent ID remains editable. The selector helps discover supported backend intents.
          </div>
        </div>
      </div>

      {/* ================= QUERY PARAMS ================= */}
      <div
        style={{
          border: "1px solid var(--border)",
          borderRadius: 14,
          padding: 14,
          background: "var(--surface)",
          marginBottom: 12,
        }}
      >
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ fontWeight: 900, fontSize: 15 }}>Query Params</div>
            <span className="pill">JSON</span>
          </div>
          <div className="subtle" style={{ marginTop: 4 }}>
            Params remain explicit JSON. No client-side semantic validation is applied.
          </div>
        </div>

        <textarea
          value={paramsText}
          onChange={(e) => {
            setParamsText(e.target.value);
            setResultsData(null);
            setResultsError(null);
          }}
          rows={10}
          style={{ width: "100%", fontFamily: "monospace" }}
          placeholder={'{\n  "key": "value"\n}'}
        />

        <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
          <button type="button" onClick={handleFormatParams}>
            Format JSON
          </button>
          <button type="button" onClick={handleResetParams}>
            Reset params
          </button>
          <button type="button" onClick={handleApplyExampleParams}>
            Apply example params
          </button>
        </div>

        {paramsError ? (
          <div style={{ marginTop: 8, color: "#b00020", fontSize: 12 }}>
            {paramsError}
          </div>
        ) : (
          <div style={{ marginTop: 8, color: "#2e7d32", fontSize: 12 }}>
            Params JSON is valid.
          </div>
        )}

        {selectedIntentEntry ? (
          <div className="subtle" style={{ marginTop: 8 }}>
            Example available for: <strong>{selectedIntentEntry.intentId}</strong>
          </div>
        ) : null}
      </div>

      {/* ================= RUN ================= */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button onClick={handleSubmit} disabled={state.loading}>
            {state.loading ? "Running..." : "Run Query Stage"}
          </button>
        </div>

        <StepStatusBanner
          status={state.status}
          loading={state.loading}
          error={state.error}
          lastRunId={state.lastRunId}
        />

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <div style={{ marginBottom: 8 }}>
              <strong>Selected statistical artifact</strong>
            </div>
            <ArtifactRefBadge
              artifactRef={state.selectedStatisticalArtifactRef}
              origin="statistical"
              copyable
            />
          </div>

          <div>
            <div style={{ marginBottom: 8 }}>
              <strong>Produced query artifact</strong>
            </div>
            <ArtifactRefBadge artifactRef={state.artifactRef} origin="query" copyable />
          </div>
        </div>
      </div>

      {/* ================= RESULTS ================= */}
      {state.status === "SUCCEEDED" ? (
        <div style={{ marginTop: 32 }}>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontWeight: 800, fontSize: 16 }}>
              Query Results
            </div>

            <div className="subtle">
              Result generated from the executed query.
            </div>
          </div>

          {resultsLoading ? (
            <div className="subtle">Loading query results...</div>
          ) : resultsError ? (
            <div style={{ color: "#b00020", fontSize: 12 }}>{resultsError}</div>
          ) : (
            <QueryResultsSection data={resultsData} />
          )}
        </div>
      ) : null}

      {/* ================= DEBUG PAYLOAD ================= */}
      <details style={{ marginTop: 16 }}>
        <summary style={{ cursor: "pointer", fontSize: 12, opacity: 0.75 }}>
          Payload preview
        </summary>

        <textarea
          value={JSON.stringify(buildPreviewPayload(), null, 2)}
          readOnly
          rows={8}
          style={{
            width: "100%",
            fontFamily: "monospace",
            fontSize: 11,
            marginTop: 8,
          }}
        />
      </details>
    </div>
    
  );
  }