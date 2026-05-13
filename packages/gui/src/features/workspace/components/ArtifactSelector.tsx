import React from "react";
import type { ArtifactRefInput } from "../model/workspaceTypes";
import { ArtifactRefBadge } from "./ArtifactRefBadge";
import { ArtifactRefInput as ArtifactRefInputForm } from "./ArtifactRefInput";
import { Stack } from "../../../components/layout/Stack";
import { Collapsible } from "../../../components/ui/Collapsible";

type ArtifactSelectorProps = {
  available: ArtifactRefInput[];
  selected: ArtifactRefInput | null;
  onSelect: (ref: ArtifactRefInput) => void;
  onManualChange: (ref: ArtifactRefInput | null) => void;
};

function getArtifactKey(ref: ArtifactRefInput): string {
  return `${ref.tool_id}::${ref.fingerprint}`;
}

function dedupeArtifacts(artifacts: ArtifactRefInput[]): ArtifactRefInput[] {
  const seen = new Set<string>();
  const result: ArtifactRefInput[] = [];

  for (const artifact of artifacts) {
    const key = getArtifactKey(artifact);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(artifact);
  }

  return result;
}

function isCompleteArtifactRef(value: ArtifactRefInput): boolean {
  return value.tool_id.trim().length > 0 && value.fingerprint.trim().length > 0;
}

export function ArtifactSelector(props: ArtifactSelectorProps) {
  const { available, selected, onSelect, onManualChange } = props;

  const normalizedAvailable = React.useMemo(
    () => dedupeArtifacts(available),
    [available]
  );

  const [manualValue, setManualValue] = React.useState<ArtifactRefInput>(
    selected ?? { tool_id: "", fingerprint: "" }
  );

  React.useEffect(() => {
    setManualValue(selected ?? { tool_id: "", fingerprint: "" });
  }, [selected]);

  function handleManualValueChange(next: ArtifactRefInput) {
    setManualValue(next);

    if (isCompleteArtifactRef(next)) {
      onManualChange({
        tool_id: next.tool_id.trim(),
        fingerprint: next.fingerprint.trim(),
      });
      return;
    }

    onManualChange(null);
  }

  return (
    <Stack gap={12}>
      <div>
        <div style={{ fontWeight: 800 }}>Available artifacts</div>
        <div className="subtle" style={{ fontSize: "var(--font-sm)", marginTop: 4 }}>
          Select an artifact produced by an upstream workspace stage.
        </div>
      </div>

      {normalizedAvailable.length === 0 ? (
        <div
          style={{
            border: "1px dashed var(--border)",
            borderRadius: "var(--r-md)",
            padding: "var(--s-3)",
            color: "var(--muted)",
            background: "color-mix(in srgb, var(--panel) 88%, black)",
          }}
        >
          No artifacts available from workspace shell.
        </div>
      ) : (
        <div style={{ display: "grid", gap: 8 }}>
          {normalizedAvailable.map((artifact) => {
            const isSelected =
              selected !== null &&
              selected.tool_id === artifact.tool_id &&
              selected.fingerprint === artifact.fingerprint;

            return (
              <button
                key={getArtifactKey(artifact)}
                type="button"
                onClick={() => onSelect(artifact)}
                style={{
                  width: "100%",
                  textAlign: "left",
                  border: isSelected
                    ? "1px solid color-mix(in srgb, var(--accent) 72%, var(--border))"
                    : "1px solid transparent",
                  borderRadius: "var(--r-md)",
                  padding: 0,
                  background: isSelected
                    ? "color-mix(in srgb, var(--accent) 8%, transparent)"
                    : "transparent",
                  cursor: "pointer",
                }}
              >
                <ArtifactRefBadge artifactRef={artifact} copyable />
              </button>
            );
          })}
        </div>
      )}

      <Collapsible
        title="Manual artifact reference"
        subtitle="Fallback input when the upstream artifact is not available in the workspace shell"
        defaultOpen={false}
        compact={true}
      >
        <ArtifactRefInputForm
          value={manualValue}
          onChange={handleManualValueChange}
        />
      </Collapsible>
    </Stack>
  );
}