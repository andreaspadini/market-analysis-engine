import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "../../../packages/gui/src/app/App";
import { ErrorBoundary } from "../../../packages/gui/src/components/feedback/ErrorBoundary";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
