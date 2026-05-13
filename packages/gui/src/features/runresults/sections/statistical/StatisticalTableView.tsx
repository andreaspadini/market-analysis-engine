import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";

type RecordRow = Record<string, unknown>;

const PRIORITY_COLUMNS = [
  "breakout_id",
  "symbol",
  "instrument",
  "timeframe",
  "breakout_time",
  "breakout_outcome",
  "side",
  "direction",
  "breakout_price",
  "balance_range_size",
  "initial_delta",
  "initial_volume",
  "atr_before",
  "follow_through",
  "max_excursion",
  "retracement_depth",
  "session_calc",
  "weekday",
  "compression_bucket",
  "delta_bucket",
  "volume_bucket",
  "atr_bucket",
];

function tryParseStructuredString(value: unknown): unknown {
  if (typeof value !== "string") return value;

  const text = value.trim();
  if (!text) return value;

  const looksStructured =
    (text.startsWith("{") && text.endsWith("}")) ||
    (text.startsWith("[") && text.endsWith("]"));

  if (!looksStructured) return value;

  try {
    return JSON.parse(text);
  } catch {
    return value;
  }
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? value.toLocaleString() : value.toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function getBadgeStyle(column: string, value: unknown): React.CSSProperties | undefined {
  if (typeof value !== "string") return undefined;

  if (column === "breakout_outcome") {
    if (value === "true_breakout") {
      return {
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 999,
        border: "1px solid rgba(80, 200, 120, 0.35)",
        background: "rgba(80, 200, 120, 0.14)",
      };
    }

    if (value === "false_breakout") {
      return {
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 999,
        border: "1px solid rgba(255, 160, 90, 0.35)",
        background: "rgba(255, 160, 90, 0.14)",
      };
    }
  }

  if (column === "side") {
    return {
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: 999,
      border: "1px solid rgba(120, 170, 255, 0.35)",
      background: "rgba(120, 170, 255, 0.14)",
    };
  }

  if (column === "direction") {
    return {
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: 999,
      border: "1px solid rgba(180, 140, 255, 0.35)",
      background: "rgba(180, 140, 255, 0.14)",
    };
  }

  return undefined;
}

function formatCell(column: string, rawValue: unknown): React.ReactNode {
  const value = tryParseStructuredString(rawValue);

  if (value === null || value === undefined) return "—";

  if (typeof value === "number") return Number.isFinite(value) ? formatNumber(value) : "—";

  if (typeof value === "boolean") return value ? "True" : "False";

  if (typeof value === "string") {
    const badgeStyle = getBadgeStyle(column, value);
    return badgeStyle ? <span style={badgeStyle}>{value}</span> : value;
  }

  if (Array.isArray(value) || typeof value === "object") {
    const preview = JSON.stringify(value);
    return (
      <details>
        <summary style={{ cursor: "pointer" }}>
          {preview.length > 80 ? `${preview.slice(0, 80)}…` : preview}
        </summary>
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, marginTop: 8 }}>{JSON.stringify(value, null, 2)}</pre>
      </details>
    );
  }

  return String(value);
}

function getColumns(records: RecordRow[]): string[] {
  const available = new Set<string>();
  for (const row of records) {
    Object.keys(row).forEach((key) => available.add(key));
  }

  const prioritized = PRIORITY_COLUMNS.filter((key) => available.has(key));
  const remaining = Array.from(available).filter((key) => !PRIORITY_COLUMNS.includes(key));

  return [...prioritized, ...remaining].slice(0, 20);
}

export function StatisticalTableView({ records }: { records: RecordRow[] }) {
  const columns = getColumns(records);
  const visibleRows = records.slice(0, 25);

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <div style={{ fontSize: 14 }}>Statistical Table</div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    style={{
                      textAlign: "left",
                      padding: "8px 10px",
                      borderBottom: "1px solid rgba(127,127,127,0.2)",
                      verticalAlign: "bottom",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {visibleRows.map((row, rowIndex) => (
                <tr key={String(row.breakout_id ?? rowIndex)}>
                  {columns.map((column) => (
                    <td
                      key={column}
                      style={{
                        padding: "8px 10px",
                        borderBottom: "1px solid rgba(127,127,127,0.12)",
                        verticalAlign: "top",
                      }}
                    >
                      {formatCell(column, row[column])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {records.length > visibleRows.length ? (
          <div style={{ marginTop: 8, fontSize: 12, opacity: 0.75 }}>
            Showing first {visibleRows.length} rows out of {records.length}.
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}