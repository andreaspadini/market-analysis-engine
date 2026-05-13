import React, { useEffect, useMemo, useRef, useState } from "react";
import { EmptyState } from "../../../components/feedback/EmptyState";
import { RootSummaryCards } from "./root/RootSummaryCards";
import { RootEventNavigator } from "./root/RootEventNavigator";
import { RootBalanceView } from "./root/RootBalanceView";
import { RootBreakoutView } from "./root/RootBreakoutView";
import { RootEventDetails } from "./root/RootEventDetails";
import { RootNestedBlocks } from "./root/RootNestedBlocks";
import { RootEvent, isRecord } from "./root/RootShared";
import { Badge, SectionCard } from "./root/RootUi";

type Props = {
  data: unknown;
};

type RootEnvelope = {
  tool_id?: unknown;
  counts?: unknown;
  events?: unknown;
};

function getEvents(data: unknown): { events: RootEvent[]; envelope: RootEnvelope | null } {
  if (Array.isArray(data)) {
    return {
      events: data.filter(isRecord),
      envelope: null,
    };
  }

  if (isRecord(data)) {
    const maybeEvents = data.events;
    if (Array.isArray(maybeEvents)) {
      return {
        events: maybeEvents.filter(isRecord),
        envelope: data,
      };
    }
  }

  return { events: [], envelope: isRecord(data) ? data : null };
}

export function RootResultsSection({ data }: Props) {
  const { events, envelope } = useMemo(() => getEvents(data), [data]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const detailRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setSelectedIndex(0);
  }, [events.length]);

  if (!data) return null;

  if (!events.length) {
    if (isRecord(data)) {
      return (
        <SectionCard title="Root Results">
          <div style={{ fontSize: 14, opacity: 0.8 }}>
            Root payload available, but no navigable event list was found.
          </div>
        </SectionCard>
      );
    }

    return <EmptyState title="No root results available" />;
  }

  const safeSelectedIndex =
    selectedIndex >= 0 && selectedIndex < events.length ? selectedIndex : 0;

  const selectedEvent = events[safeSelectedIndex];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <RootSummaryCards envelope={envelope} events={events} />

      <RootEventNavigator
        events={events}
        selectedIndex={safeSelectedIndex}
        onSelect={(index) => {
          setSelectedIndex(index);
          requestAnimationFrame(() => {
            detailRef.current?.scrollIntoView({
              behavior: "smooth",
              block: "start",
            });
          });
        }}
      />

      <div ref={detailRef} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <SectionCard title="Selected Event">
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {selectedEvent.breakout_id ? <Badge>{String(selectedEvent.breakout_id)}</Badge> : null}
              {selectedEvent.breakout_time ? (
                <Badge>{String(selectedEvent.breakout_time)}</Badge>
              ) : null}
              {selectedEvent.instrument ? <Badge>{String(selectedEvent.instrument)}</Badge> : null}
              {selectedEvent.timeframe ? <Badge>{String(selectedEvent.timeframe)}</Badge> : null}
              {selectedEvent.breakout_type ? (
                <Badge>{String(selectedEvent.breakout_type)}</Badge>
              ) : null}
            </div>

            <div style={{ fontSize: 14, opacity: 0.82 }}>
              Selected event details and nested structures are shown below.
            </div>
          </div>
        </SectionCard>

        <RootBalanceView event={selectedEvent} />
        <RootBreakoutView event={selectedEvent} />
        <RootEventDetails event={selectedEvent} />
        <RootNestedBlocks event={selectedEvent} />
      </div>
    </div>
  );
}

export default RootResultsSection;