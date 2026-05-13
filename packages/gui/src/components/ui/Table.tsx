import React from "react";

export type TableColumn = {
  key: string;
  header: React.ReactNode;
  width?: number | string;
  align?: "left" | "center" | "right";
};

export type TableRow = Record<string, React.ReactNode>;

export function Table(props: {
  columns: TableColumn[];
  rows: TableRow[];
  rowKey?: (row: TableRow, idx: number) => string;
  className?: string;
}) {
  const { columns, rows, rowKey, className } = props;

  return (
    <div className={`ui-table ${className ?? ""}`}>
      <div className="ui-table__head" role="rowgroup">
        <div className="ui-table__row ui-table__row--head" role="row">
          {columns.map((c) => (
            <div
              key={c.key}
              className="ui-table__cell ui-table__cell--head"
              role="columnheader"
              style={{
                width: c.width,
                justifyContent: c.align === "right" ? "flex-end" : c.align === "center" ? "center" : "flex-start",
              }}
            >
              {c.header}
            </div>
          ))}
        </div>
      </div>

      <div className="ui-table__body" role="rowgroup">
        {rows.map((r, idx) => (
          <div className="ui-table__row" role="row" key={rowKey?.(r, idx) ?? String(idx)}>
            {columns.map((c) => (
              <div
                key={c.key}
                className="ui-table__cell"
                role="cell"
                style={{
                  width: c.width,
                  justifyContent: c.align === "right" ? "flex-end" : c.align === "center" ? "center" : "flex-start",
                }}
              >
                {r[c.key] ?? <span className="subtle">—</span>}
              </div>
            ))}
          </div>
        ))}
      </div>

      <style>{`
        .ui-table{
          border: 1px solid var(--border);
          border-radius: var(--r-md);
          overflow: hidden;
          background: color-mix(in srgb, var(--panel) 94%, black);
        }
        .ui-table__row{
          display:flex;
          align-items: stretch;
        }
        .ui-table__row + .ui-table__row{
          border-top: 1px solid var(--border);
        }
        .ui-table__row--head{
          background: color-mix(in srgb, var(--panel-2) 85%, black);
          border-bottom: 1px solid var(--border);
        }
        .ui-table__cell{
          flex: 1 1 0;
          padding: 10px 12px;
          display:flex;
          align-items:center;
          gap: 8px;
          min-width: 0;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .ui-table__cell--head{
          font-weight: 700;
          color: color-mix(in srgb, var(--text) 90%, white);
          font-size: var(--font-sm);
          letter-spacing: .2px;
        }
      `}</style>
    </div>
  );
}
