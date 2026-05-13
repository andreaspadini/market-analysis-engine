import React from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardFooter,
} from "../../components/ui/Card";
import { Grid } from "../../components/layout/Grid";
import { Stack } from "../../components/layout/Stack";

import { useApi } from "../../api/ApiProvider";
import { useToast } from "../../app/providers/ToastProvider";
import { routes } from "../../app/routes";

import { toPipelineParametersV1 } from "./mappers/pipelineDtoMapper";
import { useRunCreationState } from "./state/useRunCreationState";

import { DatasetSection } from "./sections/DatasetSection";
import { RootEngineSection } from "./sections/RootEngineSection";
import { StatisticalSection } from "./sections/StatisticalSection";
import { QuerySection } from "./sections/QuerySection";

export function RunCreationFeature() {
  const navigate = useNavigate();
  const { o6 } = useApi();
  const { push } = useToast();

  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const runCreation = useRunCreationState();
  const { pipelineParametersV1, reset, ui } = runCreation;

  const datasetReady =
    pipelineParametersV1.dataset.instruments.length > 0 &&
    pipelineParametersV1.dataset.timeframe.trim() !== "" &&
    pipelineParametersV1.dataset.date_range.start.trim() !== "" &&
    pipelineParametersV1.dataset.date_range.end.trim() !== "";

  const ctaHint = !datasetReady
    ? ui.missingDatasetReasons.join(" • ")
    : "Dataset complete. Ready to submit.";

  const queryIntent = pipelineParametersV1.engines.query.intent_id;

  const submit = async () => {
    if (!datasetReady) return;

    try {
      setIsSubmitting(true);

      const dto = toPipelineParametersV1({ pipelineParametersV1 });

      const res = await o6.submitRun({
        api_version: "1.0",
        config: {
          config_version: "1.0",
          pipeline: { id: "demo" },
          parameters: dto,
        },
      });

      navigate(routes.results(res.run_id));
    } catch (e) {
      const err = e as any;

      push({
        title: "Submit failed",
        description: err?.error_code
          ? `${err.error_code}: ${err.message ?? "Request failed."}`
          : err?.message ?? "Request failed.",
        variant: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const datasetDateRange =
    pipelineParametersV1.dataset.date_range.start &&
    pipelineParametersV1.dataset.date_range.end
      ? `${pipelineParametersV1.dataset.date_range.start} → ${pipelineParametersV1.dataset.date_range.end}`
      : "—";

  return (
    <Grid columns="0.85fr 1.15fr 0.95fr" gap={14}>
      <Stack gap={14}>
        <DatasetSection runCreation={runCreation} />

        <Card className="print-section">
          <CardHeader>
            <CardTitle>Run Summary</CardTitle>
          </CardHeader>

          <CardContent>
            <Grid columns="1fr 1fr" gap={10}>
              <span className="pill">
                {ui.datasetIncomplete ? "Dataset incomplete" : "Ready to run"}
              </span>

              <span className="pill">
                {queryIntent ? "Query selected" : "No query"}
              </span>

              <span className="pill">
                Instruments: {pipelineParametersV1.dataset.instruments.length}
              </span>

              <span className="pill">
                Timeframe: {pipelineParametersV1.dataset.timeframe || "—"}
              </span>

              <span className="pill" style={{ gridColumn: "1 / -1" }}>
                Dates: {datasetDateRange}
              </span>

              {ui.datasetIncomplete ? (
                <span className="pill" style={{ gridColumn: "1 / -1" }}>
                  Missing: {ui.missingDatasetReasons.join(", ")}
                </span>
              ) : null}
            </Grid>
          </CardContent>

          <CardFooter>
            <Grid columns="1fr" gap={10}>
              <Button variant="secondary" onClick={reset}>
                Reset
              </Button>

              <Button
                variant="secondary"
                onClick={() => navigate(routes.patterns)}
              >
                Pattern Tool
              </Button>

              <Button
                variant="primary"
                disabled={!datasetReady || isSubmitting}
                isLoading={isSubmitting}
                onClick={submit}
              >
                Run Analysis
              </Button>

              <div
                style={{
                  fontSize: 12,
                  lineHeight: 1.4,
                  opacity: 0.85,
                  padding: "2px 2px 0",
                }}
              >
                {ctaHint}
              </div>
            </Grid>
          </CardFooter>
        </Card>
      </Stack>

      <Stack gap={14}>
        <RootEngineSection runCreation={runCreation} />
      </Stack>

      <Stack gap={14}>
        <StatisticalSection runCreation={runCreation} />
        <QuerySection runCreation={runCreation} />
      </Stack>
    </Grid>
  );
}