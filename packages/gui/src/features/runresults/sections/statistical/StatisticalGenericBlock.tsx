import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";

function renderValue(value: unknown): React.ReactNode {
  if (value === null || value === undefined) return "—";

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return "[]";

    return (
      <details>
        <summary style={{ cursor: "pointer" }}>Array ({value.length})</summary>
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, marginTop: 8 }}>
          {JSON.stringify(value, null, 2)}
        </pre>
      </details>
    );
  }

  if (typeof value === "object") {
    return (
      <details>
        <summary style={{ cursor: "pointer" }}>Object</summary>
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, marginTop: 8 }}>
          {JSON.stringify(value, null, 2)}
        </pre>
      </details>
    );
  }

  return String(value);
}

export function StatisticalGenericBlock({
  title,
  data,
}: {
  title: string;
  data: unknown;
}) {
  if (!Array.isArray(data) || data.length === 0 || typeof data[0] !== "object" || data[0] === null) {
    return null;
  }

  const first = data[0] as Record<string, unknown>;
  const nestedEntries = Object.entries(first).filter(([, value]) => {
    if (value === null || value === undefined) return false;
    return Array.isArray(value) || typeof value === "object";
  });

  if (nestedEntries.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <div style={{ fontSize: 14 }}>{title}</div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {nestedEntries.map(([key, value]) => (
            <div key={key}>
              <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{key}</div>
              <div style={{ fontSize: 12 }}>{renderValue(value)}</div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}