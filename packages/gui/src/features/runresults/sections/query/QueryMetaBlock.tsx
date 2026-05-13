import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function renderValue(value: unknown) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function renderMeta(obj: Record<string, unknown>) {
  return Object.entries(obj).map(([key, value], index, arr) => (
    <div
      key={key}
      style={{
        display: "flex",
        justifyContent: "space-between",
        gap: 12,
        padding: "6px 0",
        borderBottom: index < arr.length - 1 ? "1px solid var(--border)" : "none",
      }}
    >
      <span style={{ opacity: 0.7 }}>{key}</span>
      <span style={{ fontWeight: 500 }}>{renderValue(value)}</span>
    </div>
  ));
}

export function QueryMetaBlock({
  report,
  insight,
}: {
  report?: Record<string, unknown>;
  insight?: Record<string, unknown>;
}) {
  const reportMeta = isRecord(report?.meta) ? report.meta : undefined;
  const insightMeta = isRecord(insight?.meta) ? insight.meta : undefined;

  if (!reportMeta && !insightMeta) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Meta / Details</CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {reportMeta ? <div>{renderMeta(reportMeta)}</div> : null}
          {insightMeta ? <div>{renderMeta(insightMeta)}</div> : null}
        </div>
      </CardContent>
    </Card>
  );
}