import React from "react";
import { EmptyState } from "../../components/feedback/EmptyState";
import { RootResultsSection } from "./sections/RootResultsSection";
import { StatisticalResultsSection } from "./sections/StatisticalResultsSection";
import { QueryResultsSection } from "./sections/QueryResultsSection";
import type { ResultsSnapshot } from "./useRunResults";

type Props = {
  data: ResultsSnapshot | null;
  isLoading: boolean;
  error?: string;
};

export function ResultsSnapshotView({ data, isLoading, error }: Props) {
  if (isLoading) {
    return <div style={{ marginTop: 16 }}>Loading results...</div>;
  }

  if (error) {
    return (
      <div style={{ marginTop: 16 }}>
        <EmptyState title="Error loading results" description={error} />
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ marginTop: 16 }}>
        <EmptyState title="No results available" />
      </div>
    );
  }

  return (
    <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 16 }}>
      {data.root ? <RootResultsSection data={data.root} /> : null}

      {data.statistical ? (
        <StatisticalResultsSection data={data.statistical} />
      ) : null}

      {data.query ? <QueryResultsSection data={data.query} /> : null}
    </div>
  );
}

export default ResultsSnapshotView;