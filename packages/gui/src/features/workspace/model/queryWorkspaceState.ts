import type {
  ArtifactRefInput,
  WorkspaceStatus,
} from "./workspaceTypes";

export type QueryWorkspaceState = {
  loading: boolean;
  error: string | null;
  lastRunId: string | null;
  selectedStatisticalArtifactRef: ArtifactRefInput | null;
  artifactRef: ArtifactRefInput | null;
  status: WorkspaceStatus;
};