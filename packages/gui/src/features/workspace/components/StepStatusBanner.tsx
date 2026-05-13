import React from "react";
import type { WorkspaceStatus } from "../model/workspaceTypes";

type StepStatusBannerProps = {
  status: WorkspaceStatus;
  loading: boolean;
  error: string | null;
  lastRunId: string | null;
};

export function StepStatusBanner({
  status,
  loading,
  error,
  lastRunId,
}: StepStatusBannerProps) {
  if (error) {
    return (
      <div style={{ border: "1px solid red", padding: 8 }}>
        <strong>Error:</strong> {error}
      </div>
    );
  }

  if (loading || status === "PENDING" || status === "RUNNING") {
    return (
      <div style={{ border: "1px solid orange", padding: 8 }}>
        <strong>Running...</strong>
        {lastRunId && <div>Run ID: {lastRunId}</div>}
      </div>
    );
  }

  if (status === "SUCCEEDED") {
    return (
      <div style={{ border: "1px solid green", padding: 8 }}>
        <strong>Completed</strong>
        {lastRunId && <div>Run ID: {lastRunId}</div>}
      </div>
    );
  }

  if (status === "FAILED") {
    return (
      <div style={{ border: "1px solid red", padding: 8 }}>
        <strong>Failed</strong>
        {lastRunId && <div>Run ID: {lastRunId}</div>}
      </div>
    );
  }

  if (status === "NOT_FOUND") {
    return (
      <div style={{ border: "1px solid gray", padding: 8 }}>
        <strong>Run not found</strong>
      </div>
    );
  }

  return null;
}