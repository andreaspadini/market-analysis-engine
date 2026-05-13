import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";

type RecordRow = Record<string, unknown>;

type DistributionEntry = {
  label: string;
  count: number;
  percentage: number;
};

const PREFERRED_FIELDS = [
  "breakout_outcome",
  "side",
  "direction",
  "compression_bucket",
  "delta_bucket",
  "volume_bucket",
  "atr_bucket",
  "session_calc",
  "time_bucket",
  "weekday",
  "breakout_type",
  "confirmation_status",
];

function isPrimitiveCategory(value: unknown): value is string | number | boolean {
  return typeof value === "string" || typeof value === "number" || typeof value === "boolean";
}

function buildDistribution(records: RecordRow[], field: string): DistributionEntry[] {
  const counts = new Map<string, number>();

  for (const row of records) {
    const value = row[field];
    if (!isPrimitiveCategory(value)) continue;

    const key = String(value);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const total = Array.from(counts.values()).reduce((sum, count) => sum + count, 0);

  return Array.from(counts.entries())
    .map(([label, count]) => ({
      label,
      count,
      percentage: total > 0 ? (count / total) * 100 : 0,
    }))
    .sort((a, b) => b.count - a.count);
}

export function StatisticalDistributionView({ records }: { records: RecordRow[] }) {
  const blocks = PREFERRED_FIELDS.map((field) => ({
    field,
    entries: buildDistribution(records, field),
  })).filter((block) => block.entries.length > 1);

  if (blocks.length === 0) {
    return null;
  }

  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Distributions</div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: 12,
        }}
      >
        {blocks.map((block) => (
          <Card key={block.field}>
            <CardHeader>
              <CardTitle>
                <div style={{ fontSize: 14 }}>{block.field}</div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {block.entries.slice(0, 8).map((entry) => (
                  <div key={entry.label}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 8,
                        fontSize: 12,
                        marginBottom: 4,
                      }}
                    >
                      <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>{entry.label}</span>
                      <span>
                        {entry.count} · {entry.percentage.toFixed(1)}%
                      </span>
                    </div>

                    <div
                      style={{
                        width: "100%",
                        height: 8,
                        borderRadius: 999,
                        background: "rgba(127,127,127,0.18)",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          width: `${Math.max(entry.percentage, 2)}%`,
                          height: "100%",
                          borderRadius: 999,
                          background: "currentColor",
                          opacity: 0.35,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}