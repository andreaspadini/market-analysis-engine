import React from "react";
import { EmptyState } from "../../../../components/feedback/EmptyState";

export function QueryEmptyState() {
  return (
    <EmptyState
      title="No query results available"
      description="The query section is empty for this run."
    />
  );
}