import React from "react";
import { ErrorState } from "./ErrorState";

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    // UI-only boundary: keep side effects minimal.
    // eslint-disable-next-line no-console
    console.error("GUI ErrorBoundary caught:", error);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorState />;
    }
    return this.props.children;
  }
}
