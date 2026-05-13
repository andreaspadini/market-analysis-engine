export const routes = {
  newRun: "/run/new",
  resultsHome: "/results",
  results: (runId: string) => `/results/${runId}`,
  patterns: "/patterns",

  workspace: "/workspace",
  workspaceRoot: "/workspace/root",
  workspaceStatistical: "/workspace/statistical",
  workspaceQuery: "/workspace/query",

  workspaceRootResults: (toolId: string, fingerprint: string) =>
    `/workspace/root/${toolId}/${fingerprint}/results`,
  workspaceRootCharts: (toolId: string, fingerprint: string) =>
    `/workspace/root/${toolId}/${fingerprint}/charts`,

  // 👇 NUOVO
  workspaceStatisticalResults: (toolId: string, fingerprint: string) =>
    `/workspace/statistical/${toolId}/${fingerprint}/results`,
} as const;