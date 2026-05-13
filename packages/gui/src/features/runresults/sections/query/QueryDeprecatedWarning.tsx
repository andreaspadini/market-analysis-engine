import React from "react";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function QueryDeprecatedWarning({
  report,
}: {
  report?: Record<string, unknown>;
}) {
  const meta = isRecord(report?.meta) ? report.meta : undefined;
  const metadata = isRecord(meta?.metadata) ? meta.metadata : undefined;

  const deprecatedIntentId =
    typeof metadata?.deprecated_intent_id === "string"
      ? metadata.deprecated_intent_id
      : null;

  const replacementIntentId =
    typeof metadata?.replacement_intent_id === "string"
      ? metadata.replacement_intent_id
      : null;

  const semanticNote =
    typeof metadata?.semantic_note === "string" ? metadata.semantic_note : null;

  if (!deprecatedIntentId) {
    return null;
  }

  return (
    <div
      style={{
        border: "1px solid #f59e0b",
        background: "#fffbeb",
        padding: 12,
        borderRadius: 8,
        color: "#92400e",
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 4 }}>
        Deprecated query metric
      </div>

      <div>
        This query uses deprecated metric <strong>{deprecatedIntentId}</strong>.
        {replacementIntentId ? (
          <>
            {" "}
            Recommended: <strong>{replacementIntentId}</strong>.
          </>
        ) : null}
      </div>

      {semanticNote ? (
        <div style={{ marginTop: 6, fontSize: 12 }}>{semanticNote}</div>
      ) : null}
    </div>
  );
}