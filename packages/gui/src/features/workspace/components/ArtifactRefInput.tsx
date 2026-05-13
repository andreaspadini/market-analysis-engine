import React from "react";
import type { ArtifactRefInput as ArtifactRefValue } from "../model/workspaceTypes";
import { Stack } from "../../../components/layout/Stack";
import { FormField } from "../../../components/ui/FormField";

type ArtifactRefInputProps = {
  value: ArtifactRefValue;
  onChange: (value: ArtifactRefValue) => void;
};

export function ArtifactRefInput({
  value,
  onChange,
}: ArtifactRefInputProps) {
  return (
    <Stack gap={12}>
      <FormField
        label="Artifact tool ID"
        hint="Runtime producer identifier for the upstream artifact."
      >
        <input
          value={value.tool_id}
          onChange={(e) =>
            onChange({
              ...value,
              tool_id: e.target.value,
            })
          }
        />
      </FormField>

      <FormField
        label="Artifact fingerprint"
        hint="Unique immutable reference for the produced artifact."
      >
        <input
          value={value.fingerprint}
          onChange={(e) =>
            onChange({
              ...value,
              fingerprint: e.target.value,
            })
          }
        />
      </FormField>
    </Stack>
  );
}