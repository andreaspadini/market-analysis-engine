import React from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "./layout/AppLayout";
import { NewRunPage } from "../pages/NewRunPage";
import { ResultsPage } from "../pages/ResultsPage";
import { PatternToolPage } from "../pages/PatternToolPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { WorkspacePage } from "../pages/workspace/WorkspacePage";
import { WorkspaceRootStagePage } from "../pages/workspace/WorkspaceRootStagePage";
import { WorkspaceStatisticalStagePage } from "../pages/workspace/WorkspaceStatisticalStagePage";
import { WorkspaceQueryStagePage } from "../pages/workspace/WorkspaceQueryStagePage";
import { routes } from "./routes";
import { RootChartsPage } from "../pages/workspace/RootChartsPage";
import { RootResultsPage } from "../pages/workspace/RootResultsPage";
import { StatisticalResultsPage } from "../pages/workspace/StatisticalResultsPage";
import { StatisticalDatasetPage } from "../pages/workspace/StatisticalDatasetPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    errorElement: <NotFoundPage />,
    children: [
      { index: true, element: <Navigate to={routes.workspaceRoot} replace /> },
      { path: routes.newRun, element: <NewRunPage /> },
      { path: routes.resultsHome, element: <ResultsPage /> },
      { path: "/results/:runId", element: <ResultsPage /> },
      { path: routes.patterns, element: <PatternToolPage /> },
      {
        path: "/workspace/root/:toolId/:fingerprint/results",
        element: <RootResultsPage />,
      },
      {
        path: "/workspace/root/:toolId/:fingerprint/charts",
        element: <RootChartsPage />,
      },

      {
        path: "/workspace/statistical/:toolId/:fingerprint/results",
        element: <StatisticalResultsPage />,
      },
      {
        path: "/results/:toolId/:fingerprint/dataset",
        element: <StatisticalDatasetPage />,
      },

      {
        path: routes.workspace,
        element: <WorkspacePage />,
        children: [
          { path: "root", element: <WorkspaceRootStagePage /> },
          { path: "statistical", element: <WorkspaceStatisticalStagePage /> },
          { path: "query", element: <WorkspaceQueryStagePage /> },
        ],
      },

      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);