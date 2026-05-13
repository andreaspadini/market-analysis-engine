import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function renderValue(value: unknown) {
  if (value === null || value === undefined) {
    return "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

function renderKeyValue(obj: Record<string, unknown>) {
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
      <span style={{ fontWeight: 500, textAlign: "right" }}>{renderValue(value)}</span>
    </div>
  ));
}

export function QuerySummaryCards({
  report,
  insight,
}: {
  report?: Record<string, unknown>;
  insight?: Record<string, unknown>;
}) {
  const reportSummary = isRecord(report?.summary) ? report.summary : undefined;
  const insightSummary = isRecord(insight?.summary) ? insight.summary : undefined;

  if (!reportSummary && !insightSummary) {
    return null;
  }

  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
      {reportSummary ? (
        <div style={{ flex: "1 1 300px", minWidth: 280 }}>
          <Card>
            <CardHeader>
              <CardTitle>Report Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div>{renderKeyValue(reportSummary)}</div>
            </CardContent>
          </Card>
        </div>
      ) : null}

      {insightSummary ? (
        <div style={{ flex: "1 1 300px", minWidth: 280 }}>
          <Card>
            <CardHeader>
              <CardTitle>Insight Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div>{renderKeyValue(insightSummary)}</div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}