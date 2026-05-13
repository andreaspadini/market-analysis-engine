import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isArray(value: unknown): value is unknown[] {
  return Array.isArray(value);
}

function renderField(label: string, value: unknown) {
  if (value === null || value === undefined) return null;

  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
      <span style={{ opacity: 0.7 }}>{label}</span>
      <span style={{ fontWeight: 500 }}>
        {typeof value === "object" ? JSON.stringify(value) : String(value)}
      </span>
    </div>
  );
}

export function QueryInsightsList({
  insight,
}: {
  insight?: Record<string, unknown>;
}) {
  if (!isRecord(insight)) return null;

  const insights = insight.insights;

  if (!isArray(insights) || insights.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Insights</CardTitle>
      </CardHeader>

      <CardContent>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {insights.map((item, idx) => {
            if (!isRecord(item)) return null;

            return (
              <div
                key={idx}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  padding: 12,
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                }}
              >
                {renderField("type", item.type)}
                {renderField("classification", item.classification)}
                {renderField("dimension", item.dimension)}
                {renderField("value", item.value)}
                {renderField("metric", item.metric_value)}
                {renderField("support", item.support)}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}