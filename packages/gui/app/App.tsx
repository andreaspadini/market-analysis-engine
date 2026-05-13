import { ErrorBoundary, App as GuiApp } from "@project/gui";

export function App() {
  return (
    <ErrorBoundary>
      <GuiApp />
    </ErrorBoundary>
  );
}