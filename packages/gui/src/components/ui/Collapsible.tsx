import React from "react";

export type CollapsibleTone = "default" | "primary" | "advanced" | "readonly";

export function Collapsible(props: {
  title: React.ReactNode
  subtitle?: string;
  defaultOpen?: boolean;
  compact?: boolean;
  tone?: CollapsibleTone;
  meta?: React.ReactNode;
  children: React.ReactNode;
}) {
  const {
    title,
    subtitle,
    defaultOpen = false,
    compact = false,
    tone = "default",
    meta,
    children,
  } = props;

  const [open, setOpen] = React.useState(defaultOpen);

  return (
    <div className={`ui-collapsible ui-collapsible--${tone} ${compact ? "is-compact" : ""}`}>
      <button
        className="ui-collapsible__btn"
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <div className="ui-collapsible__copy">
          <div className="ui-collapsible__title-row">
            <div className="ui-collapsible__title">{title}</div>
            {meta ? <div className="ui-collapsible__meta">{meta}</div> : null}
          </div>
          {subtitle ? <div className="ui-collapsible__subtitle">{subtitle}</div> : null}
        </div>

        <div className={"ui-collapsible__chev" + (open ? " is-open" : "")}>▾</div>
      </button>

      {open ? <div className="ui-collapsible__body">{children}</div> : null}

      <style>{`
        .ui-collapsible{
          border: 1px solid var(--border);
          border-radius: var(--r-lg);
          overflow: hidden;
          background: color-mix(in srgb, var(--panel) 92%, black);
        }

        .ui-collapsible--primary{
          background: color-mix(in srgb, var(--panel) 88%, var(--accent) 5%);
          border-color: color-mix(in srgb, var(--border) 72%, var(--accent));
        }

        .ui-collapsible--advanced{
          background: color-mix(in srgb, var(--panel) 90%, black);
        }

        .ui-collapsible--readonly{
          background: color-mix(in srgb, var(--panel-2) 72%, black);
          border-style: dashed;
        }

        .ui-collapsible__btn{
          width: 100%;
          border: 0;
          background: transparent;
          color: var(--text);
          padding: var(--s-5);
          cursor: pointer;
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: var(--s-4);
          text-align: left;
        }

        .ui-collapsible__btn:hover{
          background: color-mix(in srgb, var(--panel-2) 55%, black);
        }

        .ui-collapsible__copy{
          min-width: 0;
        }

        .ui-collapsible__title-row{
          display: flex;
          align-items: center;
          gap: var(--s-2);
          flex-wrap: wrap;
        }

        .ui-collapsible__title{
          font-weight: 800;
          font-size: var(--font-md);
        }

        .ui-collapsible__meta{
          display: inline-flex;
          align-items: center;
          min-height: 20px;
          padding: 2px 8px;
          border: 1px solid var(--border);
          border-radius: 999px;
          color: var(--muted);
          font-size: 11px;
          line-height: 1;
          background: color-mix(in srgb, var(--panel-2) 70%, black);
        }

        .ui-collapsible__subtitle{
          margin-top: 4px;
          color: var(--muted);
          font-size: var(--font-sm);
          line-height: 1.35;
        }

        .ui-collapsible__chev{
          transition: transform .12s ease;
          color: var(--muted);
          line-height: 1;
          margin-top: 2px;
        }

        .ui-collapsible__chev.is-open{
          transform: rotate(180deg);
        }

        .ui-collapsible__body{
          padding: var(--s-5);
          border-top: 1px solid var(--border);
        }

        .ui-collapsible.is-compact .ui-collapsible__btn{
          padding: var(--s-3);
          gap: var(--s-2);
        }

        .ui-collapsible.is-compact .ui-collapsible__body{
          padding: var(--s-3);
        }

        .ui-collapsible.is-compact .ui-collapsible__title{
          font-size: var(--font-sm);
        }

        .ui-collapsible.is-compact .ui-collapsible__subtitle{
          font-size: 11px;
        }
      `}</style>
    </div>
  );
}