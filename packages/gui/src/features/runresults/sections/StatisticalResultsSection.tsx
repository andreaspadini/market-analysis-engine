import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/Card";

import { StatisticalSummaryCards } from "./statistical/StatisticalSummaryCards";
import { StatisticalDistributionView } from "./statistical/StatisticalDistributionView";
import { StatisticalTableView } from "./statistical/StatisticalTableView";
import { StatisticalGenericBlock } from "./statistical/StatisticalGenericBlock";
import { StatisticalEmptyState } from "./statistical/StatisticalEmptyState";
import { StatisticalErrorState } from "./statistical/StatisticalErrorState";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isRecordArray(value: unknown): value is Array<Record<string, unknown>> {
  return Array.isArray(value) && value.every(isRecord);
}

export function StatisticalResultsSection({ data }: { data: unknown }) {
  if (!data) {
    return <StatisticalEmptyState />;
  }

  if (!isRecordArray(data)) {
    return <StatisticalErrorState message="Statistical payload is not a valid record array" />;
  }

  if (data.length === 0) {
    return <StatisticalEmptyState />;
  }

  const records = data;
  const first = records[0] ?? {};

  const detailKeys = Object.keys(first).filter((key) => {
    const value = first[key];
    return Array.isArray(value) || isRecord(value);
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Statistical Results</CardTitle>
      </CardHeader>

      <CardContent>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <StatisticalSummaryCards records={records} />
          <StatisticalDistributionView records={records} />
          <StatisticalTableView records={records} />
          {detailKeys.length > 0 ? (
            <StatisticalGenericBlock title="Nested Statistical Blocks" data={records} />
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}