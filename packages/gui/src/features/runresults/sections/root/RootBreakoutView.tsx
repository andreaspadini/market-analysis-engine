import React from "react";
import { RootEvent } from "./RootShared";
import { Badge, FieldGrid, JsonInspector, SectionCard } from "./RootUi";

export function RootBreakoutView({ event }: { event: RootEvent }) {
  const direction = typeof event.direction === "string" ? event.direction : "";
  const directionTone =
    direction === "up" ? "up" : direction === "down" ? "down" : "default";

  const entries = ([
    ["breakout_id", event.breakout_id],
    ["breakout_time", event.breakout_time],
    ["breakout_price", event.breakout_price],
    ["boundary_price", event.boundary_price],
    ["is_failed", event.is_failed],
    ["is_retest_occurred", event.is_retest_occurred],
  ] as Array<[string, unknown]>).filter(([, value]) => value !== undefined);

  return (
    <SectionCard title="Breakout">
      <>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
          {event.breakout_type ? <Badge>{String(event.breakout_type)}</Badge> : null}
          {event.direction ? <Badge tone={directionTone}>{String(event.direction)}</Badge> : null}
          {event.boundary_type ? <Badge>{String(event.boundary_type)}</Badge> : null}
          {event.confirmation_status ? <Badge>{String(event.confirmation_status)}</Badge> : null}
        </div>

        <FieldGrid entries={entries} />

        <div style={{ marginTop: 12 }}>
          <JsonInspector title="Follow Through" value={event.follow_through} />
        </div>
      </>
    </SectionCard>
  );
}