import React from "react";
import { useOutletContext } from "react-router-dom";
import { StatisticalWorkspaceCard } from "../../features/workspace/components/StatisticalWorkspaceCard";
import type { WorkspaceShellOutletContext } from "./WorkspacePage";

export function WorkspaceStatisticalStagePage() {
  const {
    artifacts,
    prefill,
    setStatisticalArtifact,
    prefillQueryFromStatistical,
    goToQuery,
  } = useOutletContext<WorkspaceShellOutletContext>();

  const hasStatisticalArtifact = Boolean(artifacts.statistical);

  function handleArtifactProduced(
    artifact: Parameters<typeof setStatisticalArtifact>[0]
  ) {
    setStatisticalArtifact(artifact);
  }

  function handleUseInQuery() {
    prefillQueryFromStatistical(artifacts.statistical ?? null);
    goToQuery();
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <StatisticalWorkspaceCard
        availableRootArtifacts={artifacts.root ? [artifacts.root] : []}
        initialRootArtifactRef={prefill.statisticalRootArtifact}
        onArtifactProduced={handleArtifactProduced}
      />

      <div style={{ border: "1px solid #ccc", padding: 16 }}>
        <h2>Chaining</h2>
        <p>Explicitly reuse the produced statistical artifact in the Query stage.</p>

        <button
          type="button"
          onClick={handleUseInQuery}
          disabled={!hasStatisticalArtifact}
        >
          Use in Query
        </button>
      </div>
    </div>
  );
}