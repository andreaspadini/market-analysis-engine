import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { parquetReadObjects } from "hyparquet";
import { useApi } from "../../api/ApiProvider";

type ManifestOutput = {
  relpath?: string;
};

type ManifestResponse = {
  manifest?: {
    outputs?: ManifestOutput[];
  };
};

type Row = Record<string, unknown>;

function isScalarValue(value: unknown): boolean {
  return (
    value == null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  );
}

function formatCellValue(
  value: unknown,
  column?: string
): React.ReactNode {
  if (value == null) {
    return "—";
  }

  if (column === "breakout_outcome") {
    const text = String(value);

    const background =
      text === "true_breakout"
        ? "rgba(34,197,94,0.14)"
        : text === "failed_follow_through"
        ? "rgba(245,158,11,0.14)"
        : "rgba(239,68,68,0.14)";

    const border =
      text === "true_breakout"
        ? "rgba(34,197,94,0.35)"
        : text === "failed_follow_through"
        ? "rgba(245,158,11,0.35)"
        : "rgba(239,68,68,0.35)";

    const color =
      text === "true_breakout"
        ? "#22c55e"
        : text === "failed_follow_through"
        ? "#f59e0b"
        : "#ef4444";

    return (
      <span
        style={{
          padding: "3px 10px",
          borderRadius: 999,
          fontSize: 12,
          fontWeight: 600,
          border: `1px solid ${border}`,
          background,
          color,
          whiteSpace: "nowrap",
        }}
      >
        {text.replaceAll("_", " ")}
      </span>
    );
  }

  if (column === "direction") {
    const direction = String(value).toLowerCase();
    const isUp = direction === "up";

    return (
        <span
        style={{
            padding: "3px 10px",
            borderRadius: 999,
            fontSize: 12,
            fontWeight: 600,
            border: isUp
            ? "1px solid rgba(34,197,94,0.35)"
            : "1px solid rgba(239,68,68,0.35)",
            background: isUp
            ? "rgba(34,197,94,0.12)"
            : "rgba(239,68,68,0.12)",
            color: isUp ? "#22c55e" : "#ef4444",
            whiteSpace: "nowrap",
        }}
        >
        {direction.toUpperCase()}
        </span>
    );
  }

  if (column === "side") {
    return (
      <span
        style={{
          padding: "3px 10px",
          borderRadius: 999,
          fontSize: 12,
          fontWeight: 600,
          border: "1px solid rgba(255,255,255,0.12)",
          background:
            String(value).toLowerCase() === "long"
              ? "rgba(34,197,94,0.12)"
              : "rgba(239,68,68,0.12)",
          whiteSpace: "nowrap",
        }}
      >
        {String(value).toUpperCase()}
      </span>
    );
  }

  if (column === "session_calc") {
    return (
      <span
        style={{
          padding: "3px 10px",
          borderRadius: 999,
          fontSize: 12,
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(255,255,255,0.04)",
          whiteSpace: "nowrap",
        }}
      >
        {String(value).toUpperCase()}
      </span>
    );
  }

  if (column === "instrument") {
    return (
      <span
        style={{
          padding: "3px 10px",
          borderRadius: 999,
          fontSize: 12,
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(106,167,255,0.08)",
          whiteSpace: "nowrap",
        }}
      >
        {String(value)}
      </span>
    );
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? value : value.toFixed(2);
  }

  if (column === "delta_bucket") {
  const text = String(value)
    .replace("delta_", "")
    .replace("_plus", "+")
    .replaceAll("_", "–");

  return (
    <span
      style={{
        whiteSpace: "nowrap",
        fontWeight: 500,
      }}
    >
      {`Δ ${text}`}
    </span>
  );
}

if (column === "volume_bucket") {
  const text = String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <span
      style={{
        whiteSpace: "nowrap",
        fontWeight: 500,
      }}
    >
      {text}
    </span>
  );
}

  return String(value);
}

function pickPreviewColumns(rows: Row[]): string[] {
  const preferred = [
    "breakout_id",
    "breakout_time",
    "direction",
    "breakout_price",
    "breakout_outcome",
    "instrument",
    "side",
    "atr_before",
    "initial_delta",
    "delta_bucket",
    "initial_volume",
    "volume_bucket",
    "max_excursion",
    "retracement_depth",
    "session_calc",
    "weekday",
  ];

  const firstRow = rows[0];
  if (!firstRow) return [];

  const existingPreferred = preferred.filter((column) => column in firstRow);

  return existingPreferred.length > 0
    ? existingPreferred
    : Object.keys(firstRow).filter((column) =>
        rows.some((row) => isScalarValue(row[column]))
      );
}

export function StatisticalDatasetPage() {
  const { toolId, fingerprint } = useParams();
  const { http } = useApi();
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const rowsPerPage = 50;

  const columns = useMemo(() => pickPreviewColumns(rows), [rows]);
  const pageCount = Math.max(1, Math.ceil(rows.length / rowsPerPage));
  const pageStart = page * rowsPerPage;
  const pageRows = rows.slice(pageStart, pageStart + rowsPerPage);

  useEffect(() => {
    async function loadDataset() {
        if (!toolId || !fingerprint) {
        setError("Missing route parameters.");
        setLoading(false);
        return;
        }

        try {
        const manifestResponse = await http.get<ManifestResponse>(
            `/manifests/${toolId}/${fingerprint}`
            );

            const outputs = manifestResponse?.manifest?.outputs ?? [];

            const parquetOutput =
            outputs.find(
                (output) => output?.relpath === "outputs/statistical_dataset.parquet"
            ) ??
            outputs.find(
                (output) =>
                typeof output?.relpath === "string" &&
                output.relpath.endsWith(".parquet")
            );

            const resolvedRelpath = parquetOutput?.relpath;

            if (!resolvedRelpath || typeof resolvedRelpath !== "string") {
            throw new Error("Statistical parquet output not available in manifest.");
            }

            const fileBuffer = await http.get<ArrayBuffer>(
            `/artifacts/${toolId}/${fingerprint}/${resolvedRelpath}`,
            { responseType: "arraybuffer" }
            );

            const loadedRows = (await parquetReadObjects({
            file: fileBuffer,
            })) as Row[];

            setRows(loadedRows);
        } catch (e) {
            console.error("Dataset page load error", e);

            if (e instanceof Error) {
                setError(e.message);
            } else if (typeof e === "object" && e !== null) {
                setError(JSON.stringify(e, null, 2));
            } else {
                setError(String(e));
            }
            } finally {
        setLoading(false);
        }
    }

  loadDataset();
}, [http, toolId, fingerprint]);

  if (loading) {
    return <div style={{ padding: 24 }}>Loading dataset…</div>;
  }

  if (error) {
    return (
      <div style={{ padding: 24, color: "#ef4444" }}>
        Dataset error: {error}
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg)",
        color: "var(--text)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          padding: 16,
          borderBottom: "1px solid rgba(255,255,255,0.10)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 16,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>Statistical Dataset</h1>
          <p style={{ margin: "6px 0 0", opacity: 0.7, fontSize: 13 }}>
            Showing rows {pageStart + 1}–
            {Math.min(pageStart + rowsPerPage, rows.length)} of {rows.length}
          </p>
        </div>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            ← Prev
          </button>

          <span style={{ fontSize: 13, opacity: 0.75 }}>
            Page {page + 1} / {pageCount}
          </span>

          <button
            type="button"
            disabled={page >= pageCount - 1}
            onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
          >
            Next →
          </button>
        </div>
      </div>

      <div style={{ flex: 1, overflow: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: 13,
          }}
        >
          <thead>
            <tr>
              <th style={stickyCellStyle}>#</th>
              {columns.map((column) => (
                <th key={column} style={stickyCellStyle}>
                  {column}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {pageRows.map((row, index) => (
              <tr key={pageStart + index}>
                <td style={cellStyle}>{pageStart + index + 1}</td>
                {columns.map((column) => (
                  <td
                    key={column}
                    style={{
                        ...cellStyle,
                        textAlign:
                        column === "breakout_price" ||
                        column === "atr_before" ||
                        column === "initial_delta" ||
                        column === "initial_volume" ||
                        column === "max_excursion" ||
                        column === "retracement_depth"
                            ? "right"
                            : "left",
                    }}
                    >
                    {formatCellValue(row[column], column)}
                    </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const cellStyle: React.CSSProperties = {
  border: "1px solid rgba(255,255,255,0.10)",
  padding: 8,
  textAlign: "left",
  verticalAlign: "top",
  fontSize: 13,
  whiteSpace: "nowrap",
};

const stickyCellStyle: React.CSSProperties = {
  ...cellStyle,
  position: "sticky",
  top: 0,
  zIndex: 1,
  background: "var(--panel)",
};