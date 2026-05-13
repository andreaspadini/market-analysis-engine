import React from "react";
import { Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { routes } from "../../app/routes";
import type { ArtifactRefInput } from "../../features/workspace/model/workspaceTypes";

type WorkspaceArtifacts = {
  root?: ArtifactRefInput;
  statistical?: ArtifactRefInput;
  query?: ArtifactRefInput;
};

type WorkspacePrefill = {
  statisticalRootArtifact: ArtifactRefInput | null;
  queryStatisticalArtifact: ArtifactRefInput | null;
};

type WorkspaceShellOutletContext = {
  artifacts: WorkspaceArtifacts;
  prefill: WorkspacePrefill;
  setRootArtifact: (artifact: ArtifactRefInput | null) => void;
  setStatisticalArtifact: (artifact: ArtifactRefInput | null) => void;
  setQueryArtifact: (artifact: ArtifactRefInput | null) => void;
  prefillStatisticalFromRoot: (artifact: ArtifactRefInput | null) => void;
  prefillQueryFromStatistical: (artifact: ArtifactRefInput | null) => void;
  goToRoot: () => void;
  goToStatistical: () => void;
  goToQuery: () => void;
};

export function WorkspacePage() {
  const location = useLocation();
  const navigate = useNavigate();

  const [artifacts, setArtifacts] = React.useState<WorkspaceArtifacts>({});
  const [prefill, setPrefill] = React.useState<WorkspacePrefill>({
    statisticalRootArtifact: null,
    queryStatisticalArtifact: null,
  });

  const setRootArtifact = React.useCallback((artifact: ArtifactRefInput | null) => {
    setArtifacts((current) => ({
      ...current,
      root: artifact ?? undefined,
    }));
  }, []);

  const setStatisticalArtifact = React.useCallback(
    (artifact: ArtifactRefInput | null) => {
      setArtifacts((current) => ({
        ...current,
        statistical: artifact ?? undefined,
      }));
    },
    []
  );

  const setQueryArtifact = React.useCallback((artifact: ArtifactRefInput | null) => {
    setArtifacts((current) => ({
      ...current,
      query: artifact ?? undefined,
    }));
  }, []);

  const prefillStatisticalFromRoot = React.useCallback(
    (artifact: ArtifactRefInput | null) => {
      setPrefill((current) => ({
        ...current,
        statisticalRootArtifact: artifact,
      }));
    },
    []
  );

  const prefillQueryFromStatistical = React.useCallback(
    (artifact: ArtifactRefInput | null) => {
      setPrefill((current) => ({
        ...current,
        queryStatisticalArtifact: artifact,
      }));
    },
    []
  );

  const goToRoot = React.useCallback(() => {
    navigate(routes.workspaceRoot);
  }, [navigate]);

  const goToStatistical = React.useCallback(() => {
    navigate(routes.workspaceStatistical);
  }, [navigate]);

  const goToQuery = React.useCallback(() => {
    navigate(routes.workspaceQuery);
  }, [navigate]);

  if (location.pathname === routes.workspace) {
    return <Navigate to={routes.workspaceRoot} replace />;
  }

  const context: WorkspaceShellOutletContext = {
    artifacts,
    prefill,
    setRootArtifact,
    setStatisticalArtifact,
    setQueryArtifact,
    prefillStatisticalFromRoot,
    prefillQueryFromStatistical,
    goToRoot,
    goToStatistical,
    goToQuery,
  };

  return (
    <main>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 16,
        }}
      >
        {[
          { label: "Root", path: routes.workspaceRoot, onClick: goToRoot },
          { label: "Statistical", path: routes.workspaceStatistical, onClick: goToStatistical },
          { label: "Query", path: routes.workspaceQuery, onClick: goToQuery },
        ].map((item) => {
          const isActive = location.pathname === item.path;

          return (
            <button
              key={item.label}
              type="button"
              onClick={item.onClick}
              disabled={isActive}
              style={{
                padding: "6px 10px",
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 700,
                border: "1px solid var(--border)",
                background: isActive
                  ? "rgba(59,130,246,0.15)"
                  : "transparent",
                color: isActive
                  ? "#93c5fd"
                  : "var(--muted)",
                cursor: isActive ? "default" : "pointer",
              }}
            >
              {item.label}
            </button>
          );
        })}
      </div>

      <Outlet context={context} />
    </main>
  );
}

export type { WorkspaceShellOutletContext };