import React from "react";
import { EmptyState } from "../../../../components/feedback/EmptyState";

export function QueryErrorState({ message }: { message?: string }) {
  return (
    <EmptyState
      title="Query results cannot be displayed"
      description={message ?? "The query payload is not renderable."}
    />
  );
}