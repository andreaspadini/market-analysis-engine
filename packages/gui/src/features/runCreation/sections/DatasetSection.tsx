import React, { useCallback, useMemo, useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../../../components/ui/Card";
import { Stack } from "../../../components/layout/Stack";
import { Grid } from "../../../components/layout/Grid";
import { Button } from "../../../components/ui/Button";
import { Collapsible } from "../../../components/ui/Collapsible";

import { toPipelineParametersV1 } from "../mappers/pipelineDtoMapper";

import {
  listPresets,
  savePreset,
  loadPreset,
  deletePreset,
  exportPresetJson,
  importPresetJson,
} from "../presets/presetStorage";

import type { RunCreationState } from "../state/useRunCreationState";

const COMMON_INSTRUMENTS = ["ES", "NQ", "MNQ", "CL", "GC"];
const COMMON_TIMEFRAMES = ["1m", "5m", "15m", "1h", "1d"];

export function DatasetSection({
  runCreation,
}: {
  runCreation: RunCreationState;
}) {
  const {
    pipelineParametersV1,
    setDatasetField,
    replacePipelineParametersV1,
    ui,
  } = runCreation;

  const dataset = pipelineParametersV1.dataset;

  const datasetReady =
    dataset.instruments.length > 0 &&
    dataset.timeframe.trim() !== "" &&
    dataset.date_range.start.trim() !== "" &&
    dataset.date_range.end.trim() !== "";

  const missingDatasetText = ui.missingDatasetReasons.join(", ");

  // ---------- helpers ----------
  const instrumentsText = useMemo(
    () => (dataset.instruments ?? []).join("\n"),
    [dataset.instruments]
  );

  const onChangeInstruments = useCallback(
    (raw: string) => {
      const items = raw
        .split(/[\n,]+/g)
        .map((s) => s.trim())
        .filter(Boolean);
      setDatasetField("instruments", items);
    },
    [setDatasetField]
  );

  const addInstrument = useCallback(
    (instrument: string) => {
      const next = Array.from(
        new Set([...(dataset.instruments ?? []), instrument])
      );
      setDatasetField("instruments", next);
    },
    [dataset.instruments, setDatasetField]
  );

  // ---------- Presets ----------
  const [presetName, setPresetName] = useState("");
  const [selectedPresetId, setSelectedPresetId] = useState("");
  const [importName, setImportName] = useState("");
  const [importJson, setImportJson] = useState("");
  const [exportJson, setExportJson] = useState("");
  const [status, setStatus] = useState("");

  const presets = useMemo(() => listPresets(), [status]);

  const selectedPreset = useMemo(
    () => presets.find((p) => p.id === selectedPresetId) ?? null,
    [presets, selectedPresetId]
  );

  const clearStatusSoon = useCallback(() => {
    window.setTimeout(() => setStatus(""), 2500);
  }, []);

  const onSavePreset = useCallback(() => {
    try {
      const dto = toPipelineParametersV1({ pipelineParametersV1 });
      const saved = savePreset(presetName || "preset", dto);
      setStatus(`Saved preset: ${saved.name}`);
      setPresetName("");
      clearStatusSoon();
    } catch (e) {
      setStatus((e as Error).message);
    }
  }, [pipelineParametersV1, presetName, clearStatusSoon]);

  const onLoadPreset = useCallback(() => {
    try {
      if (!selectedPresetId) return;
      const dto = loadPreset(selectedPresetId);
      replacePipelineParametersV1(dto);
      setStatus("Preset loaded.");
      clearStatusSoon();
    } catch (e) {
      setStatus((e as Error).message);
    }
  }, [selectedPresetId, replacePipelineParametersV1, clearStatusSoon]);

  const onDeletePreset = useCallback(() => {
    try {
      if (!selectedPresetId) return;
      deletePreset(selectedPresetId);
      setSelectedPresetId("");
      setStatus("Preset deleted.");
      clearStatusSoon();
    } catch (e) {
      setStatus((e as Error).message);
    }
  }, [selectedPresetId, clearStatusSoon]);

  const onExportPreset = useCallback(() => {
    try {
      if (!selectedPresetId) return;
      const json = exportPresetJson(selectedPresetId);
      setExportJson(json);
      setStatus("Preset exported.");
      clearStatusSoon();
    } catch (e) {
      setStatus((e as Error).message);
    }
  }, [selectedPresetId, clearStatusSoon]);

  const onImportPreset = useCallback(() => {
    try {
      const saved = importPresetJson(importName || "imported", importJson);
      setStatus(`Imported preset: ${saved.name}`);
      setImportName("");
      setImportJson("");
      clearStatusSoon();
    } catch (e) {
      setStatus((e as Error).message);
    }
  }, [importName, importJson, clearStatusSoon]);

  return (
    <Stack gap={16}>
      <Card className="print-section">
        <CardHeader>
          <Stack gap={8}>
            <CardTitle>Dataset</CardTitle>

            <Stack direction="row" gap={8} wrap>
              <span className="pill">Required</span>
              <span className="pill">
                {datasetReady ? "Ready" : "Incomplete"}
              </span>
            </Stack>
          </Stack>
        </CardHeader>

        <CardContent>
          <Stack gap={12}>
            <div className="subtle">
              Required to start a run. Select instruments, timeframe, start date
              and end date.
            </div>

            {ui.datasetIncomplete ? (
              <div className="subtle">
                Missing: {missingDatasetText}
              </div>
            ) : (
              <div className="subtle">Dataset configuration complete.</div>
            )}

            <div>
              <div className="subtle">Instruments</div>

              <Stack direction="row" gap={8} wrap>
                {COMMON_INSTRUMENTS.map((instrument) => (
                  <Button
                    key={instrument}
                    size="sm"
                    variant="secondary"
                    onClick={() => addInstrument(instrument)}
                  >
                    {instrument}
                  </Button>
                ))}
              </Stack>

              <textarea
                value={instrumentsText}
                onChange={(e) => onChangeInstruments(e.target.value)}
                rows={3}
                placeholder="e.g. ES, NQ"
                style={{
                  width: "100%",
                  padding: 8,
                  borderRadius: 8,
                  marginTop: 8,
                }}
              />
            </div>

            <Grid columns="1fr 1fr" gap={12}>
              <div>
                <div className="subtle">Timeframe</div>
                <select
                  value={dataset.timeframe}
                  onChange={(e) => setDatasetField("timeframe", e.target.value)}
                  style={{ width: "100%", padding: 8, borderRadius: 8 }}
                >
                  <option value="">Select timeframe</option>
                  {COMMON_TIMEFRAMES.map((tf) => (
                    <option key={tf} value={tf}>
                      {tf}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <div className="subtle">Date range</div>
                <Stack direction="row" gap={8}>
                  <input
                    type="date"
                    value={dataset.date_range.start}
                    onChange={(e) =>
                      setDatasetField("date_range.start", e.target.value)
                    }
                    style={{ flex: 1, padding: 8, borderRadius: 8 }}
                  />
                  <input
                    type="date"
                    value={dataset.date_range.end}
                    onChange={(e) =>
                      setDatasetField("date_range.end", e.target.value)
                    }
                    style={{ flex: 1, padding: 8, borderRadius: 8 }}
                  />
                </Stack>
              </div>
            </Grid>
          </Stack>
        </CardContent>
      </Card>

      <Collapsible
        title="Presets & snapshots"
        subtitle="Load or save configuration snapshots"
        defaultOpen={false}
      >
        <Stack gap={14}>
          {status ? <div className="subtle">{status}</div> : null}

          <Grid columns="1fr 1fr" gap={16}>
            <Stack gap={8}>
              <div className="subtle">Save current configuration</div>

              <input
                value={presetName}
                onChange={(e) => setPresetName(e.target.value)}
                placeholder="Preset name"
                style={{ width: "100%", padding: 8, borderRadius: 8 }}
              />

              <Button variant="secondary" onClick={onSavePreset}>
                Save preset
              </Button>
            </Stack>

            <Stack gap={8}>
              <div className="subtle">Load saved configuration</div>

              <select
                value={selectedPresetId}
                onChange={(e) => setSelectedPresetId(e.target.value)}
                style={{ width: "100%", padding: 8, borderRadius: 8 }}
              >
                <option value="">Select preset</option>
                {presets.map((preset) => (
                  <option key={preset.id} value={preset.id}>
                    {preset.name}
                  </option>
                ))}
              </select>

              <Grid columns="1fr 1fr" gap={8}>
                <Button
                  variant="secondary"
                  onClick={onLoadPreset}
                  disabled={!selectedPresetId}
                >
                  Load
                </Button>

                <Button
                  variant="secondary"
                  onClick={onDeletePreset}
                  disabled={!selectedPresetId}
                >
                  Delete
                </Button>
              </Grid>
            </Stack>
          </Grid>

          {selectedPreset ? (
            <div className="subtle">
              Selected preset: {selectedPreset.name}
            </div>
          ) : null}

          <Grid columns="1fr 1fr" gap={16}>
            <Stack gap={8}>
              <div className="subtle">Export preset JSON</div>

              <Button
                variant="secondary"
                onClick={onExportPreset}
                disabled={!selectedPresetId}
              >
                Export selected preset
              </Button>

              <textarea
                value={exportJson}
                readOnly
                rows={8}
                placeholder="Exported preset JSON will appear here"
                style={{ width: "100%", padding: 8, borderRadius: 8 }}
              />
            </Stack>

            <Stack gap={8}>
              <div className="subtle">Import preset JSON</div>

              <input
                value={importName}
                onChange={(e) => setImportName(e.target.value)}
                placeholder="Imported preset name"
                style={{ width: "100%", padding: 8, borderRadius: 8 }}
              />

              <textarea
                value={importJson}
                onChange={(e) => setImportJson(e.target.value)}
                rows={8}
                placeholder="Paste preset JSON here"
                style={{ width: "100%", padding: 8, borderRadius: 8 }}
              />

              <Button
                variant="secondary"
                onClick={onImportPreset}
                disabled={!importJson.trim()}
              >
                Import preset
              </Button>
            </Stack>
          </Grid>
        </Stack>
      </Collapsible>
    </Stack>
  );
}