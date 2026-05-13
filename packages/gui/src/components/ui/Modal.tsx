import React from "react";
import { createPortal } from "react-dom";
import { Button } from "./Button";

export function Modal(props: {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children?: React.ReactNode;
  footer?: React.ReactNode;
}) {
  const { open, title, description, onClose, children, footer } = props;
  const ref = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  React.useEffect(() => {
    if (open) {
      // focus first focusable element (minimal)
      window.setTimeout(() => {
        const el = ref.current?.querySelector<HTMLElement>('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])');
        el?.focus();
      }, 0);
    }
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div className="ui-modal__overlay" role="dialog" aria-modal="true" onMouseDown={onClose}>
      <div className="ui-modal__panel" onMouseDown={(e) => e.stopPropagation()} ref={ref}>
        <div className="ui-modal__head">
          <div>
            <div className="ui-modal__title">{title}</div>
            {description ? <div className="ui-modal__desc subtle">{description}</div> : null}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
        </div>
        <div className="ui-modal__body">{children}</div>
        {footer ? <div className="ui-modal__footer">{footer}</div> : null}
      </div>

      <style>{`
        .ui-modal__overlay{
          position: fixed; inset: 0;
          background: rgba(0,0,0,.55);
          display:flex;
          align-items:center;
          justify-content:center;
          padding: var(--s-5);
          z-index: 60;
        }
        .ui-modal__panel{
          width: min(720px, 100%);
          background: var(--panel);
          border: 1px solid var(--border);
          border-radius: var(--r-lg);
          box-shadow: var(--shadow);
          overflow:hidden;
        }
        .ui-modal__head{
          padding: var(--s-5);
          border-bottom: 1px solid var(--border);
          display:flex;
          align-items:flex-start;
          justify-content:space-between;
          gap: var(--s-4);
          background: color-mix(in srgb, var(--panel) 92%, black);
        }
        .ui-modal__title{ font-weight: 800; font-size: var(--font-lg); }
        .ui-modal__desc{ margin-top: 6px; }
        .ui-modal__body{ padding: var(--s-5); }
        .ui-modal__footer{
          padding: var(--s-5);
          border-top: 1px solid var(--border);
          background: color-mix(in srgb, var(--panel) 92%, black);
        }
      `}</style>
    </div>,
    document.body
  );
}
