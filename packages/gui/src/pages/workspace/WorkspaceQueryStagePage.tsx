import React from "react";
import { useOutletContext } from "react-router-dom";
import { QueryWorkspaceCard } from "../../features/workspace/components/QueryWorkspaceCard";
import type { WorkspaceShellOutletContext } from "./WorkspacePage";

export function WorkspaceQueryStagePage() {
  const { artifacts, prefill, setQueryArtifact } =
    useOutletContext<WorkspaceShellOutletContext>();

  return (
    <QueryWorkspaceCard
        availableStatisticalArtifacts={
            artifacts.statistical ? [artifacts.statistical] : []
        }
        initialStatisticalArtifactRef={prefill.queryStatisticalArtifact}
        onArtifactProduced={setQueryArtifact}
        />
  );
}