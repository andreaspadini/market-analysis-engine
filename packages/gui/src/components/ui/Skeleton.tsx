import React from "react";

export function Skeleton(props: { height?: number; width?: number | string; radius?: number; className?: string }) {
  const { height = 12, width = "100%", radius = 12, className } = props;

  return (
    <div
      className={`ui-skel ${className ?? ""}`}
      style={{ height, width, borderRadius: radius }}
      aria-hidden
    >
      <style>{`
        .ui-skel{
          background: linear-gradient(
            90deg,
            color-mix(in srgb, var(--panel-2) 75%, black),
            color-mix(in srgb, var(--panel) 70%, black),
            color-mix(in srgb, var(--panel-2) 75%, black)
          );
          background-size: 200% 100%;
          animation: skel 1.2s ease-in-out infinite;
          border: 1px solid var(--border);
        }
        @keyframes skel{
          0%{ background-position: 0% 0; }
          100%{ background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
}
