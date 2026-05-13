import React from "react";
import { PageShell } from "../app/layout/PageShell";
import { Button } from "../components/ui/Button";
import { Stack } from "../components/layout/Stack";
import { useToast } from "../app/providers/ToastProvider";
import { RunCreationFeature } from "../features/runCreation/RunCreationFeature";

export function NewRunPage() {
  const { push } = useToast();

  return (
    <PageShell
      title=""
      description="Setup your run: configure dataset, review parameters, and execute."
      actions={
        <Stack direction="row" gap={10}>
          <Button
            variant="secondary"
            onClick={() =>
              push({
                title: "Presets info",
                description: "Presets are stored locally as strict DTO snapshots.",
              })
            }
          >
            Presets Info
          </Button>
        </Stack>
      }
    >
      <RunCreationFeature />
    </PageShell>
  );
}