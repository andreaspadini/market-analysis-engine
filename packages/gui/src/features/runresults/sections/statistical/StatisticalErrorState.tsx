import React from "react";
import { EmptyState } from "../../../../components/feedback/EmptyState";

export function StatisticalErrorState({ message }: { message?: string }) {
  return (
    <EmptyState
      title="Unable to render statistical results"
      description={message ?? "The statistical payload shape is not supported."}
    />
  );
}