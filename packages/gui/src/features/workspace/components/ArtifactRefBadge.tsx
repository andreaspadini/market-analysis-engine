import React from "react";
import type { ArtifactRefInput } from "../model/workspaceTypes";
import { Button } from "../../../components/ui/Button";

type ArtifactOrigin = "root" | "statistical" | "query";

type ArtifactRefBadgeProps = {
  artifactRef: ArtifactRefInput | null;
  origin?: ArtifactOrigin;
  copyable?: boolean;
};

function toCanonicalArtifactRefJson(artifactRef: ArtifactRefInput): string {
  return JSON.stringify(
    {
      tool_id: artifactRef.tool_id,
      fingerprint: artifactRef.fingerprint,
    },
    null,
    2
  );
}

function truncateFingerprint(fingerprint: string): string {
  if (fingerprint.length <= 16) return fingerprint;
  return `${fingerprint.slice(0, 8)}...${fingerprint.slice(-8)}`;
}

export function ArtifactRefBadge({
  artifactRef,
  origin,
  copyable = false,
}: ArtifactRefBadgeProps) {
  if (!artifactRef) {
    return (
      <div className="artifact-ref-badge artifact-ref-badge--empty">
        <div className="artifact-ref-badge__title">Artifact reference</div>
        <div className="artifact-ref-badge__muted">Not available</div>

        <style>{styles}</style>
      </div>
    );
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(toCanonicalArtifactRefJson(artifactRef));
    } catch {
      // silent fallback
    }
  };

  return (
    <div className="artifact-ref-badge">
      <div className="artifact-ref-badge__main">
        {origin ? <span className="artifact-ref-badge__origin">{origin}</span> : null}

        <div className="artifact-ref-badge__row">
          <span className="artifact-ref-badge__label">Tool</span>
          <code>{artifactRef.tool_id}</code>
        </div>

        <div className="artifact-ref-badge__row">
          <span className="artifact-ref-badge__label">Fingerprint</span>
          <code title={artifactRef.fingerprint}>
            {truncateFingerprint(artifactRef.fingerprint)}
          </code>
        </div>
      </div>

      {copyable ? (
        <Button type="button" variant="ghost" size="sm" onClick={handleCopy}>
          Copy JSON
        </Button>
      ) : null}

      <style>{styles}</style>
    </div>
  );
}

const styles = `
  .artifact-ref-badge{
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--s-3);
    border: 1px solid var(--border);
    border-radius: var(--r-md);
    padding: var(--s-3);
    background: color-mix(in srgb, var(--panel-2) 78%, black);
    color: var(--text);
  }

  .artifact-ref-badge--empty{
    border-style: dashed;
    color: var(--muted);
  }

  .artifact-ref-badge__main{
    min-width: 0;
    display: grid;
    gap: 5px;
  }

  .artifact-ref-badge__title{
    font-weight: 800;
  }

  .artifact-ref-badge__muted,
  .artifact-ref-badge__label{
    color: var(--muted);
  }

  .artifact-ref-badge__origin{
    width: fit-content;
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 2px 8px;
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .04em;
  }

  .artifact-ref-badge__row{
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    font-size: var(--font-sm);
  }

  .artifact-ref-badge code{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
`;