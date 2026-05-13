import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import * as Papa from "papaparse";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useApi } from "../../api/ApiProvider";
import { routes } from "../../app/routes";
import { Cell } from "recharts";

function parseCSV(text: string) {
  const result = Papa.parse(text, {
    header: true,
    skipEmptyLines: true,
  });

  return result.data as Record<string, string>[];
}

function SummaryTooltip(props: any) {
  const { active, payload, label } = props;

  if (!active || !payload || !payload.length) {
    return null;
  }

  const item = payload[0]?.payload;

  return (
    <div
      style={{
        background: "#111827",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: 10,
        padding: "10px 12px",
        fontSize: 13,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      <div>Value: {item?.value ?? 0}</div>
      <div>
        Percent: {typeof item?.pct === "number" ? item.pct.toFixed(1) : "0.0"}%
      </div>
    </div>
  );
}

function SummaryLabel(props: any) {
  const { x, y, width, value, payload } = props;

  if (!payload) return null;

  const pct =
    typeof payload.pct === "number" ? `${payload.pct.toFixed(0)}%` : "";

  return (
    <text
      x={x + width / 2}
      y={y - 6}
      fill="#d1d5db"
      textAnchor="middle"
      fontSize={12}
    >
      {pct}
    </text>
  );
}

export function RootResultsPage() {
  const { toolId, fingerprint } = useParams();
  const { http } = useApi();

  const [rows, setRows] = useState<Record<string, string>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const total = rows.length;
  const failed = rows.filter((r) => String(r.is_failed).trim() === "True").length;
  const success = total - failed;
  const up = rows.filter((r) => r.direction === "up").length;
  const down = rows.filter((r) => r.direction === "down").length;

  const summaryChartData = [
    { name: "Total", value: total, pct: 100 },
    {
      name: "Failed",
      value: failed,
      pct: total > 0 ? (failed / total) * 100 : 0,
    },
    {
      name: "Success",
      value: success,
      pct: total > 0 ? (success / total) * 100 : 0,
    },
    {
      name: "Up",
      value: up,
      pct: total > 0 ? (up / total) * 100 : 0,
    },
    {
      name: "Down",
      value: down,
      pct: total > 0 ? (down / total) * 100 : 0,
    },
  ];

  useEffect(() => {
    async function loadData() {
      if (!toolId || !fingerprint) {
        setError("Missing route parameters.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const manifestResponse = await http.get<any>(
          `/manifests/${toolId}/${fingerprint}`
        );

        const outputs = manifestResponse?.manifest?.outputs ?? [];

        const rootCsvOutput = outputs.find(
          (output: any) => output?.relpath === "outputs/root_output_dataset.csv"
        );

        const relpath = rootCsvOutput?.relpath;

        if (!relpath || typeof relpath !== "string") {
          throw new Error("Root output CSV not available in manifest.");
        }

        const text = await http.get<string>(
          `/artifacts/${toolId}/${fingerprint}/${relpath}`
        );

        const parsed = parseCSV(text);
        setRows(parsed);
      } catch (err: any) {
        setError(err?.message ?? "Failed to load root results.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [toolId, fingerprint, http]);

  function handleOpenCharts() {
    if (!toolId || !fingerprint) return;

    const url = routes.workspaceRootCharts(toolId, fingerprint);
    window.open(url, "_blank", "noopener,noreferrer");
  }

  if (loading) {
    return <div style={{ padding: 24 }}>Loading root results...</div>;
  }

  if (error) {
    return (
      <div style={{ padding: 24, color: "red" }}>
        Error: {error}
      </div>
    );
  }

  return (
    <div
      style={{
        padding: 24,
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 16,
          padding: 16,
          background: "rgba(255,255,255,0.02)",
          marginBottom: 20,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 16,
            flexWrap: "wrap",
            marginBottom: 14,
          }}
        >
          <div style={{ opacity: 0.75, fontSize: 13 }}>
            {fingerprint && <span>Run: {fingerprint.slice(0, 10)}</span>}
          </div>

          <div
            style={{
              display: "flex",
              gap: 14,
              flexWrap: "wrap",
              fontSize: 13,
              opacity: 0.8,
              alignItems: "center",
            }}
          >
            <span>Total: {total}</span>
            <span>F: {failed}</span>
            <span>S: {success}</span>
            <span>Up: {up}</span>
            <span>Down: {down}</span>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            flexWrap: "wrap",
            marginBottom: 10,
          }}
        >
          <h2 style={{ margin: 0, fontSize: 18 }}>Summary</h2>

          <button
            onClick={handleOpenCharts}
            style={{
              padding: "8px 12px",
              borderRadius: 10,
              border: "1px solid rgba(255,255,255,0.16)",
              background: "rgba(255,255,255,0.04)",
              color: "inherit",
              cursor: "pointer",
            }}
          >
            Open Charts
          </button>
        </div>

        <div
          style={{
            width: "100%",
            height: 220,
            marginBottom: 8,
          }}
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={summaryChartData}
              margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip content={<SummaryTooltip />} />
              <Bar dataKey="value" label={<SummaryLabel />}>
                {summaryChartData.map((entry, index) => {
                  let fill = "#3b82f6";

                  if (entry.name === "Failed") fill = "#ef4444";
                  if (entry.name === "Success") fill = "#22c55e";
                  if (entry.name === "Up") fill = "#86efac";
                  if (entry.name === "Down") fill = "#fca5a5";

                  return <Cell key={`cell-${index}`} fill={fill} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div
        style={{
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 16,
          padding: 16,
          background: "rgba(255,255,255,0.02)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            flexWrap: "wrap",
            marginBottom: 10,
          }}
        >
          <h2 style={{ margin: 0, fontSize: 18 }}>Breakouts</h2>
          <p style={{ margin: 0, opacity: 0.7, fontSize: 13 }}>
            Showing first {Math.min(rows.length, 100)} of {rows.length} rows
          </p>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                <th style={cellStyle}>#</th>
                <th style={cellStyle}>direction</th>
                <th style={cellStyle}>breakout_price</th>
                <th style={cellStyle}>is_failed</th>
                <th style={cellStyle}>initial_delta</th>
                <th style={cellStyle}>initial_volume</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 100).map((row, index) => (
                <tr
                  key={`${row.breakout_id ?? "row"}-${index}`}
                  style={{
                    background:
                      String(row.is_failed).trim() === "True"
                        ? "rgba(255, 140, 0, 0.08)"
                        : "transparent",
                  }}
                >
                  <td style={cellStyle}>{index + 1}</td>
                  <td style={cellStyle}>{row.direction}</td>
                  <td style={cellStyle}>{row.breakout_price}</td>
                  <td style={cellStyle}>{row.is_failed}</td>
                  <td style={cellStyle}>{row.initial_delta}</td>
                  <td style={cellStyle}>{row.initial_volume}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const cellStyle: React.CSSProperties = {
  border: "1px solid rgba(255,255,255,0.12)",
  padding: 8,
  textAlign: "left",
  verticalAlign: "top",
  fontSize: 13,
};