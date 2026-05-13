import React from "react";
import type { UiRunStatus } from "./useRunStatus";

type Props = {
  status: UiRunStatus;
  isPolling: boolean;
  error?: string;
};

function toneFor(status: UiRunStatus): "neutral" | "running" | "success" | "failed" {
  switch (status) {
    case "RUNNING":
      return "running";
    case "SUCCEEDED":
      return "success";
    case "FAILED":
    case "NOT_FOUND":
      return "failed";
    default:
      return "neutral";
  }
}

export function RunStatusView({ status, isPolling, error }: Props) {
  const tone = toneFor(status);

  const title =
    status === "NOT_FOUND"
      ? "Run not found"
      : status === "PENDING"
      ? "Pending"
      : status === "RUNNING"
      ? "Running"
      : status === "SUCCEEDED"
      ? "Succeeded"
      : "Failed";

  const showSpinner = isPolling && !["SUCCEEDED", "FAILED", "NOT_FOUND"].includes(status);

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span>
          {tone === "running"
            ? "🔵"
            : tone === "success"
            ? "🟢"
            : tone === "failed"
            ? "🔴"
            : "⚪"}
        </span>

        <strong>{title}</strong>

        {showSpinner ? <span>⏳</span> : null}
      </div>

      {status === "NOT_FOUND" ? (
        <div style={{ opacity: 0.8 }}>This run may be volatile or already cleaned up.</div>
      ) : null}

      {error ? <div style={{ opacity: 0.8 }}>Error: {error}</div> : null}
    </div>
  );
}

// ✅ export default “di comodo” (così non rompi se importi default)
export default RunStatusView;