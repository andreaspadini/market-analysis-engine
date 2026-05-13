import React from "react";

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <section className={`ui-card ${className ?? ""}`}>
      {children}
      <style>{`
        .ui-card{
          background: var(--panel);
          border: 1px solid var(--border);
          border-radius: var(--r-lg);
          box-shadow: var(--shadow);
          overflow: hidden;
        }
      `}</style>
    </section>
  );
}

export function CardHeader({ children }: { children: React.ReactNode }) {
  return (
    <div className="ui-card__hdr">
      {children}
      <style>{`
        .ui-card__hdr{
          padding: var(--s-4);
          border-bottom: 1px solid var(--border);
          background: color-mix(in srgb, var(--panel) 90%, black);
        }
      `}</style>
    </div>
  );
}

export function CardTitle({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: "var(--font-lg)", fontWeight: 700 }}>{children}</div>;
}

export function CardContent({ children }: { children: React.ReactNode }) {
  return <div style={{ padding: "var(--s-4)" }}>{children}</div>;
}

export function CardFooter({ children }: { children: React.ReactNode }) {
  return (
    <div className="ui-card__ftr">
      {children}
      <style>{`
        .ui-card__ftr{
          padding: var(--s-4);
          border-top: 1px solid var(--border);
          background: color-mix(in srgb, var(--panel) 92%, black);
        }
      `}</style>
    </div>
  );
}
