import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/Card";
import { Table, TableColumn, TableRow } from "../../../../components/ui/Table";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isArray(value: unknown): value is unknown[] {
  return Array.isArray(value);
}

function toTableRows(data: unknown[]): TableRow[] {
  return data.map((item) => {
    if (!isRecord(item)) return {};

    const row: TableRow = {};

    for (const [key, value] of Object.entries(item)) {
      if (value === null || value === undefined) {
        row[key] = "—";
      } else if (typeof value === "object") {
        row[key] = JSON.stringify(value);
      } else {
        row[key] = String(value);
      }
    }

    return row;
  });
}

function extractColumns(rows: TableRow[]): TableColumn[] {
  if (!rows.length) return [];

  const keys = Object.keys(rows[0]);

  return keys.map((key) => ({
    key,
    header: key,
  }));
}

export function QueryRankingTable({
  report,
}: {
  report?: Record<string, unknown>;
}) {
  if (!isRecord(report)) return null;

  const ranking = report.ranking;
  const data = report.data;

  let rowsSource: unknown[] | undefined;

  // 🔹 Caso A: ranking
  if (isArray(ranking) && ranking.length > 0) {
    rowsSource = ranking;
  }

  // 🔹 Caso B: fallback su data
  else if (isArray(data) && data.length > 0) {
    rowsSource = data;
  }

  if (!rowsSource) return null;

  const rows = toTableRows(rowsSource);
  const columns = extractColumns(rows);

  if (!columns.length) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ranking / Results</CardTitle>
      </CardHeader>
      <CardContent>
        <Table columns={columns} rows={rows} />
      </CardContent>
    </Card>
  );
}