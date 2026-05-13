import React from "react";
import { RootEvent, isPrimitive } from "./RootShared";
import { FieldGrid, JsonInspector, SectionCard } from "./RootUi";

export function RootBalanceView({ event }: { event: RootEvent }) {
  const entries = Object.entries(event).filter(([key, value]) => {
    if (!key.startsWith("balance_")) return false;
    return isPrimitive(value);
  }) as Array<[string, unknown]>;

  const fullEntries: Array<[string, unknown]> = [
    ...entries,
    ["parent_balance_id", event.parent_balance_id] as [string, unknown],
  ].filter(([, value]) => value !== undefined && value !== null);

  return (
    <SectionCard title="Balance">
      <>
        <FieldGrid entries={fullEntries} />
        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <JsonInspector title="Balance HVN" value={event.balance_hvn} />
          <JsonInspector title="Balance LVN" value={event.balance_lvn} />
        </div>
      </>
    </SectionCard>
  );
}