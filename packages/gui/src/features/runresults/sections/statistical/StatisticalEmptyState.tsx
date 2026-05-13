import React from "react";
import { EmptyState } from "../../../../components/feedback/EmptyState";

export function StatisticalEmptyState() {
  return (
    <EmptyState
      title="No statistical results available"
      description="No statistical payload was provided for this run."
    />
  );
}