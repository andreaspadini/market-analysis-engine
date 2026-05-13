import React from "react";

export type InfoBlockTone = "info" | "warning" | "danger" | "success" | "readonly";

export function InfoBlock(props: {
  title?: React.ReactNode;
  children: React.ReactNode;
  tone?: InfoBlockTone;
  compact?: boolean;
  className?: string;
}) {
  const { title, children, tone = "info", compact = false, className } = props;

  return (
    <div className={`ui-info-block ui-info-block--${tone} ${compact ? "is-compact" : ""} ${className ?? ""}`}>
      {title ? <div className="ui-info-block__title">{title}</div> : null}
      <div className="ui-info-block__body">{children}</div>

      <style>{`
        .ui-info-block{
          border: 1px solid var(--border);
          border-radius: var(--r-md);
          padding: var(--s-3);
          background: color-mix(in srgb, var(--panel-2) 72%, black);
          color: var(--muted);
          line-height: 1.4;
        }

        .ui-info-block.is-compact{
          padding: var(--s-2);
          font-size: var(--font-sm);
        }

        .ui-info-block__title{
          color: var(--text);
          font-weight: 800;
          margin-bottom: 4px;
        }

        .ui-info-block--info{
          border-color: color-mix(in srgb, var(--border) 78%, var(--accent));
        }

        .ui-info-block--warning{
          border-color: color-mix(in srgb, #eab308 55%, var(--border));
          background: color-mix(in srgb, #eab308 9%, var(--panel));
        }

        .ui-info-block--danger{
          border-color: color-mix(in srgb, var(--danger) 55%, var(--border));
          background: color-mix(in srgb, var(--danger) 9%, var(--panel));
        }

        .ui-info-block--success{
          border-color: color-mix(in srgb, #22c55e 55%, var(--border));
          background: color-mix(in srgb, #22c55e 8%, var(--panel));
        }

        .ui-info-block--readonly{
          border-style: dashed;
          background: color-mix(in srgb, var(--panel) 84%, black);
        }

        .ui-info-block__body{
          font-size: var(--font-sm);
        }
      `}</style>
    </div>
  );
}