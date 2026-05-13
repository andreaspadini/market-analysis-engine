import React from "react";
import { RootEvent, isPrimitive } from "./RootShared";
import { FieldGrid, SectionCard } from "./RootUi";

export function RootEventDetails({ event }: { event: RootEvent }) {
  const excludedKeys = new Set([
    "breakout_id",
    "breakout_time",
    "breakout_price",
    "breakout_type",
    "direction",
    "boundary_type",
    "boundary_price",
    "confirmation_status",
    "is_failed",
    "is_retest_occurred",
    "follow_through",
    "parent_balance_id",
    "balance_high",
    "balance_low",
    "balance_midpoint",
    "balance_range_size",
    "balance_vpoc",
    "balance_hvn",
    "balance_lvn",
  ]);

  const entries = Object.entries(event).filter(
    ([key, value]) => !excludedKeys.has(key) && isPrimitive(value)
  ) as Array<[string, unknown]>;

  if (!entries.length) return null;

  return (
    <SectionCard title="Event Details">
      <FieldGrid entries={entries} />
    </SectionCard>
  );
}