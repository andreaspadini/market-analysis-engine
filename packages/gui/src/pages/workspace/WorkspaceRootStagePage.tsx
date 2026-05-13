import React from "react";
import { useOutletContext } from "react-router-dom";
import { RootWorkspaceCard } from "../../features/workspace/components/RootWorkspaceCard";
import type { WorkspaceShellOutletContext } from "./WorkspacePage";

export function WorkspaceRootStagePage() {
  const {
    setRootArtifact,
    prefillStatisticalFromRoot,
    goToStatistical,
    artifacts,
  } = useOutletContext<WorkspaceShellOutletContext>();

  const hasRootArtifact = Boolean(artifacts.root);

  function handleArtifactProduced(artifact: Parameters<typeof setRootArtifact>[0]) {
    setRootArtifact(artifact);
  }

  function handleUseInStatistical() {
    prefillStatisticalFromRoot(artifacts.root ?? null);
    goToStatistical();
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <RootWorkspaceCard onArtifactProduced={handleArtifactProduced} />

      <div style={{ border: "1px solid #ccc", padding: 16 }}>
        <h2>Chaining</h2>
        <p>Explicitly reuse the produced root artifact in the Statistical stage.</p>

        <button
          type="button"
          onClick={handleUseInStatistical}
          disabled={!hasRootArtifact}
        >
          Use in Statistical
        </button>
      </div>
    </div>
  );
}