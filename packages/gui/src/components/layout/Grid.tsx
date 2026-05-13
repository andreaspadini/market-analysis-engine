import React from "react";

export function Grid(props: {
  columns?: string;
  gap?: number;
  children: React.ReactNode;
  className?: string;
}) {
  const { columns = "1fr", gap = 16, children, className } = props;
  return (
    <div className={className} style={{ display: "grid", gridTemplateColumns: columns, gap }}>
      {children}
    </div>
  );
}
