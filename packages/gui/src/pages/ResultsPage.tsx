import React from "react";
import { useParams } from "react-router-dom";

import { useRunStatus } from "../features/runresults/useRunStatus";
import { useRunResults } from "../features/runresults/useRunResults";
import { RunStatusView } from "../features/runresults/RunStatusView";
import { ResultsSnapshotView } from "../features/runresults/ResultsSnapshotView";

export function ResultsPage() {
  const { runId } = useParams<{ runId: string }>();

  const safeRunId = runId ?? "";

  const { status, isPolling, error } = useRunStatus(safeRunId);
  const {
    data,
    isLoading: isResultsLoading,
    error: resultsError,
  } = useRunResults(safeRunId, status === "SUCCEEDED");

  return (
    <div style={{ padding: 16 }}>
      <RunStatusView status={status} isPolling={isPolling} error={error} />

      <ResultsSnapshotView
        data={data}
        isLoading={isResultsLoading}
        error={resultsError}
      />
    </div>
  );
}

export default ResultsPage;