import type {
  ArtifactRefInput,
  WorkspaceStatus,
} from "./workspaceTypes";

export type RootWorkspaceState = {
  loading: boolean;
  error: string | null;
  lastRunId: string | null;
  artifactRef: ArtifactRefInput | null;
  status: WorkspaceStatus;
};