import React from "react";

export function ContentContainer({ children }: { children: React.ReactNode }) {
  return <div className="container">{children}</div>;
}
