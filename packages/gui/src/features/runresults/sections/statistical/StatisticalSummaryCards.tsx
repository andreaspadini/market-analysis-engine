import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";

type RecordRow = Record<string, unknown>;

function asPrimitive(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return Number.isFinite(value) ? value.toLocaleString() : "—";
  if (typeof value === "boolean") return value ? "True" : "False";
  if (typeof value === "string") return value || "—";
  return "—";
}

function countDistinct(records: RecordRow[], key: string): number {
  const values = new Set(
    records
      .map((row) => row[key])
      .filter((value) => value !== null && value !== undefined && typeof value !== "object"),
  );
  return values.size;
}

function mostCommonPrimitive(records: RecordRow[], key: string): string {
  const counts = new Map<string, number>();

  for (const row of records) {
    const raw = row[key];
    if (raw === null || raw === undefined || typeof raw === "object") continue;
    const value = String(raw).trim();
    if (!value) continue;
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }

  let winner = "—";
  let best = -1;

  for (const [value, count] of counts.entries()) {
    if (count > best) {
      winner = value;
      best = count;
    }
  }

  return winner;
}

function firstPrimitive(records: RecordRow[], key: string): string {
  for (const row of records) {
    const value = row[key];
    if (value === null || value === undefined || typeof value === "object") continue;
    const text = String(value).trim();
    if (text) return text;
  }
  return "—";
}

function getTimeRange(records: RecordRow[]): string {
  const values = records
    .map((row) => row.breakout_time)
    .filter((value): value is string => typeof value === "string" && value.length > 0);

  if (values.length === 0) return "—";

  const sorted = [...values].sort();
  const first = sorted[0];
  const last = sorted[sorted.length - 1];

  if (first === last) return first;
  return `${first} → ${last}`;
}

export function StatisticalSummaryCards({ records }: { records: RecordRow[] }) {
  const primarySymbol = mostCommonPrimitive(records, "symbol");
  const primaryInstrument = mostCommonPrimitive(records, "instrument");
  const displaySymbol = primarySymbol !== "—" ? primarySymbol : primaryInstrument;

  const cards = [
    { label: "Rows", value: records.length.toLocaleString() },
    { label: "Primary Symbol", value: displaySymbol },
    { label: "Primary Instrument", value: primaryInstrument },
    { label: "Primary Timeframe", value: mostCommonPrimitive(records, "timeframe") },
    { label: "Schema Version", value: firstPrimitive(records, "schema_version") },
    { label: "Outcomes", value: countDistinct(records, "breakout_outcome").toString() },
    { label: "Sessions", value: countDistinct(records, "session_calc").toString() },
    { label: "Time Range", value: getTimeRange(records) },
  ];

  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Overview</div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 12,
        }}
      >
        {cards.map((card) => (
          <Card key={card.label}>
            <CardHeader>
              <CardTitle>
                <div style={{ fontSize: 14 }}>{card.label}</div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div style={{ fontSize: 14, lineHeight: 1.4 }}>{asPrimitive(card.value)}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}