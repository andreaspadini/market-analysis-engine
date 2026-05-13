import React from "react";

export type TabsItem = { key: string; label: string; content: React.ReactNode };

export function Tabs(props: {
  items: TabsItem[];
  value?: string;
  defaultValue?: string;
  onChange?: (key: string) => void;
}) {
  const { items, value, defaultValue, onChange } = props;
  const isControlled = value !== undefined;
  const [internal, setInternal] = React.useState(defaultValue ?? items[0]?.key);

  const active = isControlled ? value! : internal!;
  const setActive = (k: string) => {
    if (!isControlled) setInternal(k);
    onChange?.(k);
  };

  const current = items.find(i => i.key === active) ?? items[0];

  return (
    <div className="ui-tabs">
      <div className="ui-tabs__list" role="tablist" aria-label="Tabs">
        {items.map(it => (
          <button
            key={it.key}
            className={"ui-tabs__tab" + (it.key === active ? " is-active" : "")}
            role="tab"
            aria-selected={it.key === active}
            onClick={() => setActive(it.key)}
            type="button"
          >
            {it.label}
          </button>
        ))}
      </div>
      <div className="ui-tabs__panel" role="tabpanel">
        {current?.content}
      </div>

      <style>{`
        .ui-tabs{ display:flex; flex-direction:column; gap: var(--s-3); }
        .ui-tabs__list{
          display:flex;
          gap: var(--s-2);
          flex-wrap: wrap;
          border-bottom: 1px solid var(--border);
          padding-bottom: var(--s-2);
        }
        .ui-tabs__tab{
          border: 1px solid var(--border);
          border-radius: 999px;
          background: transparent;
          color: var(--muted);
          padding: 8px 12px;
          cursor: pointer;
          transition: background .12s ease, border-color .12s ease;
        }
        .ui-tabs__tab:hover{ border-color: color-mix(in srgb, var(--border) 50%, var(--accent)); color: var(--text); }
        .ui-tabs__tab.is-active{
          background: color-mix(in srgb, var(--accent) 18%, var(--panel));
          border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
          color: var(--text);
        }
        .ui-tabs__panel{ min-height: 40px; }
      `}</style>
    </div>
  );
}
