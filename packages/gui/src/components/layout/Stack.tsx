import React from "react";

export function Stack(props: {
  direction?: "row" | "column";
  gap?: number;
  align?: React.CSSProperties["alignItems"];
  justify?: React.CSSProperties["justifyContent"];
  wrap?: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  const { direction = "column", gap = 12, align, justify, wrap, children, className } = props;
  return (
    <div
      className={className}
      style={{
        display: "flex",
        flexDirection: direction,
        gap,
        alignItems: align,
        justifyContent: justify,
        flexWrap: wrap ? "wrap" : "nowrap",
      }}
    >
      {children}
    </div>
  );
}
