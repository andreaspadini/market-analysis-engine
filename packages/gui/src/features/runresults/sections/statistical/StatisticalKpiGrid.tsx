import React from "react";
import { Card, CardContent } from "../../../../components/ui/Card";

function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return "n/a";
  return value.toFixed(digits);
}

function formatOneDecimal(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "n/a";
  return value.toFixed(1);
}

function formatPercent(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "n/a";
  return `${value.toFixed(1)}%`;
}

export function StatisticalKpiGrid({
  total,
  targetColumns,
  avgMaxExcursion,
  avgBreakoutEfficiency,
  cleanQuantRate,
}: {
  total: number;
  targetColumns: number;
  avgMaxExcursion: number | null;
  avgBreakoutEfficiency: number | null;
  cleanQuantRate: number | null;
}) {
  const items = [
    {
      label: "Events Analyzed",
      value: total.toLocaleString(),
      description: "Root breakout events processed by the Statistical pipeline.",
    },
    {
      label: "Target Levels",
      value: targetColumns.toLocaleString(),
      description: "Configured target and scan output columns detected in the dataset.",
    },
    {
      label: "Avg Max Excursion",
      value: `${formatOneDecimal(avgMaxExcursion)} pts`,
      description: "Average maximum favorable movement after breakout.",
    },
    {
      label: "Avg Breakout Efficiency",
      value: `${formatNumber(avgBreakoutEfficiency)}x`,
      description: "Average breakout extension relative to pre-breakout ATR.",
    },
    {
      label: "Clean Quant Rate",
      value: formatPercent(cleanQuantRate),
      description: "Share of events confirmed as clean quantitative moves.",
    },
  ];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: "var(--s-3)",
        marginBottom: "var(--s-4)",
      }}
    >
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent>
            <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>
              {item.label}
            </div>

            <div
              style={{
                fontSize: "var(--font-xl)",
                fontWeight: 750,
                lineHeight: 1.1,
              }}
            >
              {item.value}
            </div>

            <div
              style={{
                fontSize: 12,
                color: "var(--muted)",
                marginTop: 8,
                lineHeight: 1.35,
              }}
            >
              {item.description}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}