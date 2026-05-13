import React from "react";
import { RootEvent, formatLabel, isRecord } from "./RootShared";
import { JsonInspector, SectionCard } from "./RootUi";

export function RootNestedBlocks({ event }: { event: RootEvent }) {
  const excludedKeys = new Set(["follow_through", "balance_hvn", "balance_lvn"]);

  const nestedEntries = Object.entries(event).filter(([key, value]) => {
    if (excludedKeys.has(key)) return false;
    if (value === null || value === undefined) return false;
    return Array.isArray(value) || isRecord(value);
  });

  if (!nestedEntries.length) return null;

  return (
    <SectionCard title="Nested Data">
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {nestedEntries.map(([key, value]) => (
          <JsonInspector key={key} title={formatLabel(key)} value={value} />
        ))}
      </div>
    </SectionCard>
  );
}