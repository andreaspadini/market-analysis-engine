import type {
  ArtifactRefInput,
  WorkspaceStatus,
} from "./workspaceTypes";

export type StatisticalWorkspaceState = {
  loading: boolean;
  error: string | null;
  lastRunId: string | null;
  selectedRootArtifactRef: ArtifactRefInput | null;
  artifactRef: ArtifactRefInput | null;
  status: WorkspaceStatus;
};