import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

export function EmptyState(props: { title: string; description?: string; children?: React.ReactNode }) {
  const { title, description, children } = props;
  return (
    <Card className="print-section">
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>
        {description ? <div className="subtle" style={{ marginBottom: 14 }}>{description}</div> : null}
        {children}
      </CardContent>
    </Card>
  );
}
