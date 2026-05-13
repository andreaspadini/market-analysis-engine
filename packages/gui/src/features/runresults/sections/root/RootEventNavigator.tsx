import React from "react";
import { RootEvent, getNumberField, getStringField } from "./RootShared";
import { Badge, SectionCard } from "./RootUi";

export function RootEventNavigator({
  events,
  selectedIndex,
  onSelect,
}: {
  events: RootEvent[];
  selectedIndex: number;
  onSelect: (index: number) => void;
}) {
  return (
    <SectionCard title="Events">
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {events.map((event, index) => {
          const selected = selectedIndex === index;
          const breakoutTime = getStringField(event, "breakout_time");
          const instrument = getStringField(event, "instrument", "symbol");
          const timeframe = getStringField(event, "timeframe");
          const direction = getStringField(event, "direction");
          const breakoutType = getStringField(event, "breakout_type");
          const breakoutPrice = getNumberField(event, "breakout_price");
          const breakoutId = getStringField(event, "breakout_id");

          const directionTone =
            direction === "up" ? "up" : direction === "down" ? "down" : "default";

          return (
            <button
              key={`${breakoutId}-${index}`}
              type="button"
              onClick={() => onSelect(index)}
              aria-pressed={selected}
              style={{
                textAlign: "left",
                width: "100%",
                border: selected
                  ? "1px solid rgba(255,255,255,0.45)"
                  : "1px solid rgba(255,255,255,0.14)",
                borderRadius: 12,
                padding: 14,
                background: selected ? "rgba(255,255,255,0.10)" : "rgba(255,255,255,0.02)",
                color: "#f8fafc",
                cursor: "pointer",
                transition: "background 120ms ease, border-color 120ms ease",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 12,
                  marginBottom: 10,
                }}
              >
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <Badge>{breakoutTime}</Badge>
                  <Badge>{instrument}</Badge>
                  <Badge>{timeframe}</Badge>
                  <Badge tone={directionTone}>{direction}</Badge>
                  <Badge>{breakoutType}</Badge>
                </div>

                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    color: selected ? "#ffffff" : "rgba(248,250,252,0.78)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {selected ? "Selected event" : "Click to inspect"}
                </div>
              </div>

              <div
                style={{
                  fontSize: 13,
                  color: "#e2e8f0",
                  fontWeight: 500,
                }}
              >
                {breakoutId}
                {breakoutPrice !== null ? ` · ${breakoutPrice}` : ""}
              </div>
            </button>
          );
        })}
      </div>
    </SectionCard>
  );
}