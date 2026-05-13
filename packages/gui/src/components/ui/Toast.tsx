import React from "react";

export type ToastVariant = "info" | "success" | "warning" | "error";

export type ToastItem = {
  id: string;
  title: string;
  description?: string;
  variant: ToastVariant;
};

function iconFor(v: ToastVariant) {
  switch (v) {
    case "success": return "✓";
    case "warning": return "!";
    case "error": return "×";
    default: return "i";
  }
}

export function ToastViewport(props: { items: ToastItem[]; onDismiss: (id: string) => void }) {
  const { items, onDismiss } = props;

  return (
    <div className="ui-toast__viewport no-print" aria-live="polite" aria-relevant="additions">
      {items.map((t) => (
        <div key={t.id} className={`ui-toast ui-toast--${t.variant}`} role="status">
          <div className="ui-toast__icon" aria-hidden>{iconFor(t.variant)}</div>
          <div className="ui-toast__content">
            <div className="ui-toast__title">{t.title}</div>
            {t.description ? <div className="ui-toast__desc subtle">{t.description}</div> : null}
          </div>
          <button className="ui-toast__close" onClick={() => onDismiss(t.id)} aria-label="Dismiss">×</button>
        </div>
      ))}

      <style>{`
        .ui-toast__viewport{
          position: fixed;
          right: 18px;
          bottom: 18px;
          display:flex;
          flex-direction:column;
          gap: 10px;
          z-index: 80;
          width: min(420px, calc(100vw - 36px));
        }
        .ui-toast{
          display:flex;
          gap: 12px;
          align-items:flex-start;
          padding: 12px 12px;
          border-radius: var(--r-md);
          border: 1px solid var(--border);
          background: color-mix(in srgb, var(--panel) 92%, black);
          box-shadow: var(--shadow);
        }
        .ui-toast__icon{
          width: 26px; height: 26px;
          border-radius: 10px;
          display:flex; align-items:center; justify-content:center;
          border: 1px solid var(--border);
          background: color-mix(in srgb, var(--panel-2) 80%, black);
          flex: 0 0 auto;
          font-weight: 900;
        }
        .ui-toast__title{ font-weight: 800; }
        .ui-toast__desc{ margin-top: 2px; }
        .ui-toast__close{
          margin-left:auto;
          border: 1px solid transparent;
          background: transparent;
          color: var(--muted);
          cursor:pointer;
          border-radius: 10px;
          width: 28px; height: 28px;
        }
        .ui-toast__close:hover{ border-color: var(--border); color: var(--text); }
        .ui-toast--success{ border-color: color-mix(in srgb, #25c48a 45%, var(--border)); }
        .ui-toast--warning{ border-color: color-mix(in srgb, #ffb020 45%, var(--border)); }
        .ui-toast--error{ border-color: color-mix(in srgb, var(--danger) 55%, var(--border)); }
      `}</style>
    </div>
  );
}
