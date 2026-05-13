import React from "react";
import { RootEvent, isRecord } from "./RootShared";
import { FieldGrid, SectionCard } from "./RootUi";

type RootEnvelope = {
  tool_id?: unknown;
  counts?: unknown;
  events?: unknown;
};

export function RootSummaryCards({
  envelope,
  events,
}: {
  envelope: RootEnvelope | null;
  events: RootEvent[];
}) {
  const first = events[0] ?? {};
  const counts = isRecord(envelope?.counts) ? envelope.counts : null;

  const entries = ([
    ["total_events", events.length],
    ["instrument", first.instrument],
    ["symbol", first.symbol],
    ["timeframe", first.timeframe],
    ["version", first.version],
    ["tool_id", envelope?.tool_id],
    ["breakouts", counts?.breakouts],
    ["balances", counts?.balances],
    ["bars", counts?.bars],
  ] as Array<[string, unknown]>).filter(([, value]) => value !== undefined && value !== null);

  return (
    <SectionCard title="Root Summary">
      <FieldGrid entries={entries} />
    </SectionCard>
  );
}