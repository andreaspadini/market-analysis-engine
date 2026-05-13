import React from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md";

export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
}) {
  const { variant = "primary", size = "md", isLoading, className, children, disabled, ...rest } = props;
  const isDisabled = disabled || isLoading;

  return (
    <button
      {...rest}
      className={`ui-btn ui-btn--${variant} ui-btn--${size} ${className ?? ""}`}
      disabled={isDisabled}
      aria-busy={isLoading ? true : undefined}
    >
      {isLoading ? <span className="ui-btn__spinner" aria-hidden /> : null}
      <span className="ui-btn__label">{children}</span>

      <style>{`
        .ui-btn{
          border: 1px solid var(--border);
          border-radius: 12px;
          padding: 10px 14px;
          background: var(--panel-2);
          color: var(--text);
          cursor: pointer;
          display:inline-flex;
          align-items:center;
          gap:10px;
          box-shadow: none;
          transition: transform .02s ease, background .12s ease, border-color .12s ease;
          user-select: none;
        }
        .ui-btn:hover{ border-color: color-mix(in srgb, var(--border) 50%, var(--accent)); }
        .ui-btn:active{ transform: translateY(1px); }

        .ui-btn--sm{ padding: 8px 12px; font-size: var(--font-sm); border-radius: 11px; }
        .ui-btn--md{ font-size: var(--font-md); }

        .ui-btn--primary{
          background: color-mix(in srgb, var(--accent) 30%, var(--panel-2));
          border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
        }
        .ui-btn--secondary{
          background: color-mix(in srgb, var(--panel) 85%, black);
        }
        .ui-btn--ghost{
          background: transparent;
        }
        .ui-btn--danger{
          background: color-mix(in srgb, var(--danger) 18%, var(--panel-2));
          border-color: color-mix(in srgb, var(--danger) 40%, var(--border));
        }

        .ui-btn:disabled{
          opacity: .55;
          cursor: not-allowed;
        }

        .ui-btn__spinner{
          width: 14px;
          height: 14px;
          border-radius: 999px;
          border: 2px solid var(--border);
          border-top-color: var(--accent);
          animation: spin .9s linear infinite;
        }
        @keyframes spin{ to{ transform: rotate(360deg); } }
      `}</style>
    </button>
  );
}
