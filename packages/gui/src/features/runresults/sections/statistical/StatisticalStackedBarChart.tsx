import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";

type StackedBarDatum = {
  name: string;
  true_breakout?: number;
  failed_follow_through?: number;
  false_breakout?: number;
};

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) {
    return null;
  }

  return (
    <div
      style={{
        background: "var(--panel)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-md)",
        padding: "var(--s-3)",
        boxShadow: "var(--shadow)",
        fontSize: "var(--font-sm)",
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 6 }}>{label}</div>

      {payload.map((entry: any) => (
        <div key={entry.dataKey} style={{ marginBottom: 4 }}>
          {entry.name}: {entry.value}
        </div>
      ))}
    </div>
  );
}

export function StatisticalStackedBarChart({
  title,
  data,
}: {
  title: string;
  data: StackedBarDatum[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <div style={{ fontSize: 14 }}>{title}</div>
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div style={{ width: "100%", height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "var(--muted)" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "var(--muted)" }} />
              <Tooltip content={<CustomTooltip />} />

              <Bar
                dataKey="true_breakout"
                stackId="outcome"
                name="True breakout"
                fill="#22c55e"
              />
              <Bar
                dataKey="failed_follow_through"
                stackId="outcome"
                name="Failed follow through"
                fill="#f59e0b"
              />
              <Bar
                dataKey="false_breakout"
                stackId="outcome"
                name="False breakout"
                fill="#ef4444"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}