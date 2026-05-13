import React from "react";
import { PageShell } from "../app/layout/PageShell";
import { Button } from "../components/ui/Button";
import { routes } from "../app/routes";
import { Stack } from "../components/layout/Stack";
import { useNavigate } from "react-router-dom";

export function NotFoundPage() {
  const nav = useNavigate();
  return (
    <PageShell title="Page not found" description="The route does not exist in this GUI V1 shell.">
      <Stack direction="row" gap={10}>
        <Button variant="secondary" onClick={() => nav(routes.newRun)}>Go to New Run</Button>
      </Stack>
    </PageShell>
  );
}
