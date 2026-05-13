import React from "react";

export function QueryResultsSection({ data }: { data: any }) {
  const report = data?.report;
  const insight = data?.insight;

  const ranking = Array.isArray(report?.ranking)
    ? report.ranking
    : Array.isArray(report?.data)
      ? report.data
      : [];

  const summary = report?.summary ?? insight?.summary ?? {};

  const metricName =
    report?.meta?.metric ??
    insight?.meta?.metric ??
    report?.meta?.source_metric ??
    "metric";

  const hasGroupedResults = ranking.length > 0;

  const sortedRanking = [...ranking].sort(
    (a: any, b: any) => Number(readRowMetric(b) ?? 0) - Number(a.result ?? 0)
  );

  const bestRow = sortedRanking[0];
  const worstRow = sortedRanking[sortedRanking.length - 1];

  const singleValue =
    report?.result ??
    report?.value ??
    report?.data?.result ??
    report?.data?.value ??
    null;

  return (
    <div style={{ marginTop: 24 }}>
      {/* ================= OVERVIEW ================= */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 8 }}>
          Overview
        </div>

        <div style={{ display: "flex", gap: 16 }}>
          <SummaryCard label="Total rows" value={summary.rows_total} />
          <SummaryCard label="Valid rows" value={summary.rows_valid} />
        </div>
      </div>

      {/* ================= GROUPED RESULTS ================= */}
      {hasGroupedResults ? (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 8 }}>
            Results by group
          </div>

          <div
            style={{
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: 10,
              overflow: "hidden",
            }}
          >
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", fontSize: 12, opacity: 0.7 }}>
                  <th style={{ padding: 10 }}>Group</th>
                  <th style={{ padding: 10 }}>{formatLabel(String(metricName))}</th>
                  <th style={{ padding: 10 }}>Total rows</th>
                  <th style={{ padding: 10 }}>Valid rows</th>
                </tr>
              </thead>

              <tbody>
                {ranking.map((row: any, index: number) => {
                  const numericResults = ranking
                    .map((r: any) => Number(r.result))
                    .filter((v: number) => Number.isFinite(v));

                  const maxResult =
                    numericResults.length > 0 ? Math.max(...numericResults) : null;
                  const minResult =
                    numericResults.length > 0 ? Math.min(...numericResults) : null;

                  const rowResult = Number(row.result);
                  const isTop = maxResult !== null && rowResult === maxResult;
                  const isBottom = minResult !== null && rowResult === minResult;

                  return (
                    <tr
                      key={index}
                      style={{
                        background: isTop
                          ? "rgba(80, 200, 120, 0.08)"
                          : isBottom
                            ? "rgba(255, 80, 80, 0.08)"
                            : "transparent",
                        borderTop: "1px solid rgba(255,255,255,0.05)",
                      }}
                    >
                      <td style={{ padding: 10 }}>{formatGroup(row.group_key)}</td>

                      <td style={{ padding: 10, fontWeight: 800 }}>
                        {formatMetricValue(readRowMetric(row), metricName)}
                      </td>

                      <td style={{ padding: 10 }}>{row.rows_total ?? "—"}</td>
                      <td style={{ padding: 10 }}>{row.rows_valid ?? "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : singleValue !== null ? (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 8 }}>
            Result
          </div>

          <SummaryCard
            label={formatLabel(String(metricName))}
            value={formatMetricValue(singleValue, String(metricName))}
          />
        </div>
      ) : (
        <div style={{ marginBottom: 24 }} className="subtle">
          No tabular result was returned for this query. Open Technical details to inspect the raw output.
        </div>
      )}

      {/* ================= INSIGHTS ================= */}
      {hasGroupedResults ? (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontWeight: 800, fontSize: 16, marginBottom: 8 }}>
            Key insights
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 10,
            }}
          >
            <InsightSummaryCard
              title="Best group"
              group={formatGroup(bestRow?.group_key)}
              value={bestRow?.result}
              rows={bestRow?.rows_valid}
              metricName={String(metricName)}
            />

            <InsightSummaryCard
              title="Weakest group"
              group={formatGroup(worstRow?.group_key)}
              value={worstRow?.result}
              rows={worstRow?.rows_valid}
              metricName={String(metricName)}
            />

            <InsightSummaryCard
              title="Difference"
              group="Best minus weakest"
              value={
                typeof bestRow?.result === "number" &&
                typeof worstRow?.result === "number"
                  ? bestRow.result - worstRow.result
                  : Number.isFinite(Number(bestRow?.result)) &&
                      Number.isFinite(Number(worstRow?.result))
                    ? Number(bestRow.result) - Number(worstRow.result)
                    : null
              }
              rows={summary.rows_valid}
              metricName={String(metricName)}
            />
          </div>
        </div>
      ) : null}

      {/* ================= TECHNICAL DETAILS ================= */}
      <details style={{ opacity: 0.65 }}>
        <summary style={{ cursor: "pointer", fontSize: 12 }}>
          Technical details
        </summary>

        <pre
          style={{
            marginTop: 10,
            fontSize: 11,
            background: "rgba(0,0,0,0.3)",
            padding: 10,
            borderRadius: 6,
            overflow: "auto",
          }}
        >
          {JSON.stringify({ report, insight }, null, 2)}
        </pre>
      </details>
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: unknown }) {
  return (
    <div
      style={{
        flex: 1,
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 10,
        padding: 12,
        background: "rgba(255,255,255,0.02)",
      }}
    >
      <div style={{ fontSize: 12, opacity: 0.7 }}>{label}</div>
      <div style={{ fontWeight: 900, fontSize: 18 }}>{String(value ?? "—")}</div>
    </div>
  );
}

function InsightSummaryCard({
  title,
  group,
  value,
  rows,
  metricName,
}: {
  title: string;
  group: string;
  value: unknown;
  rows: unknown;
  metricName: string;
}) {
  return (
    <div
      style={{
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: 10,
        padding: 12,
        background: "rgba(255,255,255,0.02)",
      }}
    >
      <div style={{ fontWeight: 800 }}>{title}</div>

      <div style={{ fontSize: 12, opacity: 0.7, marginTop: 4 }}>
        {group}
      </div>

      <div style={{ marginTop: 8, fontWeight: 900, fontSize: 18 }}>
        {formatMetricValue(value, metricName)}
      </div>

      <div style={{ fontSize: 11, opacity: 0.6 }}>
        Valid rows: {String(rows ?? "—")}
      </div>
    </div>
  );
}

function formatMetricValue(value: unknown, metricName: string) {
  const numeric =
    typeof value === "number"
      ? value
      : typeof value === "string"
        ? Number(value)
        : NaN;

  if (!Number.isFinite(numeric)) {
    return "—";
  }

  const lowerMetric = metricName.toLowerCase();

  if (
    lowerMetric.includes("rate") ||
    lowerMetric.includes("ratio") ||
    lowerMetric.includes("probability")
  ) {
    return `${(numeric * 100).toFixed(2)}%`;
  }

  return numeric.toFixed(4);
}

function formatGroup(group: unknown) {
  if (!group) return "—";

  if (typeof group === "string") {
    try {
      const parsed = JSON.parse(group) as Record<string, unknown>;
      const key = Object.keys(parsed)[0];

      return key ? `${formatLabel(key)}: ${String(parsed[key])}` : group;
    } catch {
      return group;
    }
  }

  if (typeof group === "object" && !Array.isArray(group)) {
    const parsed = group as Record<string, unknown>;
    const key = Object.keys(parsed)[0];

    return key ? `${formatLabel(key)}: ${String(parsed[key])}` : "—";
  }

  return String(group);
}

function formatLabel(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
function readRowMetric(row: any) {
  return (
    row.result ??
    row.value ??
    row.metric ??
    row.probability ??
    row.ratio ??
    row.count ??
    row.score ??
    null
  );
}