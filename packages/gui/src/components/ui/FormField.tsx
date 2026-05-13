import React from "react";

export type FormFieldTone = "default" | "warning" | "danger" | "success";

export function FormField(props: {
  label: React.ReactNode;
  children: React.ReactNode;
  hint?: React.ReactNode;
  example?: React.ReactNode;
  note?: React.ReactNode;
  tone?: FormFieldTone;
  className?: string;
}) {
  const {
    label,
    children,
    hint,
    example,
    note,
    tone = "default",
    className,
  } = props;

  return (
    <div className={`ui-form-field ui-form-field--${tone} ${className ?? ""}`}>
      <div className="ui-form-field__label">{label}</div>
      {hint ? <div className="ui-form-field__hint">{hint}</div> : null}
      <div className="ui-form-field__control">{children}</div>
      {example ? <div className="ui-form-field__example">{example}</div> : null}
      {note ? <div className="ui-form-field__note">{note}</div> : null}

      <style>{`
        .ui-form-field{
          display: flex;
          flex-direction: column;
          gap: 6px;
          min-width: 0;
        }

        .ui-form-field__label{
          color: var(--text);
          font-size: var(--font-sm);
          font-weight: 700;
          letter-spacing: .01em;
        }

        .ui-form-field__hint,
        .ui-form-field__example,
        .ui-form-field__note{
          color: var(--muted);
          font-size: var(--font-sm);
          line-height: 1.35;
        }

        .ui-form-field__example{
          opacity: .88;
        }

        .ui-form-field__note{
          border-left: 2px solid var(--border);
          padding-left: 8px;
        }

        .ui-form-field--warning .ui-form-field__note{
          border-left-color: color-mix(in srgb, #eab308 70%, var(--border));
          color: color-mix(in srgb, #eab308 72%, var(--text));
        }

        .ui-form-field--danger .ui-form-field__note{
          border-left-color: var(--danger);
          color: color-mix(in srgb, var(--danger) 75%, var(--text));
        }

        .ui-form-field--success .ui-form-field__note{
          border-left-color: color-mix(in srgb, #22c55e 70%, var(--border));
          color: color-mix(in srgb, #22c55e 70%, var(--text));
        }

        .ui-form-field__control > input,
        .ui-form-field__control > select,
        .ui-form-field__control > textarea{
          width: 100%;
          border: 1px solid var(--border);
          border-radius: var(--r-sm);
          background: color-mix(in srgb, var(--panel-2) 82%, black);
          color: var(--text);
          padding: 9px 10px;
          min-height: 38px;
        }

        .ui-form-field__control > textarea{
          min-height: 96px;
          resize: vertical;
        }

        .ui-form-field__control > input:focus,
        .ui-form-field__control > select:focus,
        .ui-form-field__control > textarea:focus{
          outline: none;
          border-color: color-mix(in srgb, var(--accent) 65%, var(--border));
          box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 16%, transparent);
        }
      `}</style>
    </div>
  );
}