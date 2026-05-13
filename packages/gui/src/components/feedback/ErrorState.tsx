import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Button } from "../ui/Button";
import { Stack } from "../layout/Stack";

export function ErrorState(props: { title?: string; description?: string; onReload?: () => void }) {
  const { title = "Something went wrong", description = "A UI error occurred. Please reload the page.", onReload } = props;

  return (
    <Card className="print-section">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Stack gap={14}>
          <div className="subtle">{description}</div>
          <div>
            <Button variant="secondary" onClick={onReload ?? (() => window.location.reload())}>Reload</Button>
          </div>
        </Stack>
      </CardContent>
    </Card>
  );
}
