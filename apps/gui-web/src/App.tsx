import React from "react";
import { ErrorBoundary, App as GuiApp, ApiProvider } from "@project/gui";
import { getEnv } from "./env";

export function App() {
  const env = getEnv();

  return (
    <ErrorBoundary>
      <ApiProvider baseUrl={env.O6_BASE_URL}>
        <GuiApp />
      </ApiProvider>
    </ErrorBoundary>
  );
}