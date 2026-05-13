import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";
import { compactPreview, formatLabel, formatValue, isRecord } from "./RootShared";

export function FieldGrid({ entries }: { entries: Array<[string, unknown]> }) {
  if (!entries.length) return null;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: 12,
      }}
    >
      {entries.map(([key, value]) => (
        <div
          key={key}
          style={{
            border: "1px solid var(--border, #e5e7eb)",
            borderRadius: 10,
            padding: 12,
          }}
        >
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 6 }}>{formatLabel(key)}</div>
          <div style={{ fontSize: 14, fontWeight: 600, wordBreak: "break-word" }}>
            {formatValue(value)}
          </div>
        </div>
      ))}
    </div>
  );
}

export function SectionCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export function Badge({
  children,
  tone = "default",
}: {
  children: React.ReactNode;
  tone?: "default" | "up" | "down";
}) {
  const styles =
    tone === "up"
      ? {
          border: "1px solid rgba(34,197,94,0.35)",
          background: "rgba(34,197,94,0.10)",
          color: "#bbf7d0",
        }
      : tone === "down"
      ? {
          border: "1px solid rgba(248,113,113,0.35)",
          background: "rgba(248,113,113,0.10)",
          color: "#fecaca",
        }
      : {
          border: "1px solid rgba(255,255,255,0.16)",
          background: "rgba(255,255,255,0.04)",
          color: "#f8fafc",
        };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "4px 8px",
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
        ...styles,
      }}
    >
      {children}
    </span>
  );
}

export function JsonInspector({ title, value }: { title: string; value: unknown }) {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value) && value.length === 0) return null;
  if (isRecord(value) && Object.keys(value).length === 0) return null;

  return (
    <details
      style={{
        border: "1px solid var(--border, #e5e7eb)",
        borderRadius: 10,
        padding: 12,
      }}
    >
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>
        {title} · {compactPreview(value)}
      </summary>

      <pre
        style={{
          marginTop: 12,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          fontSize: 12,
          lineHeight: 1.5,
        }}
      >
        {JSON.stringify(value, null, 2)}
      </pre>
    </details>
  );
}