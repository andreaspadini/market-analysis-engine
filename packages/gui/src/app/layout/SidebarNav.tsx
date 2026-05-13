import React from "react";
import { NavLink, type NavLinkRenderProps } from "react-router-dom";
import { routes } from "../routes";
import { ContentContainer } from "./ContentContainer";

const items = [
  { to: routes.workspaceRoot, label: "Root", hint: "Root stage execution" },
  { to: routes.workspaceStatistical, label: "Statistical", hint: "Statistical stage execution" },
  { to: routes.workspaceQuery, label: "Query", hint: "Query stage execution" },
];

export function SidebarNav() {
  return (
    <aside className="app-shell__sidebar no-print">
      <ContentContainer>
        <nav className="nav">
          {items.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              className={({ isActive }: NavLinkRenderProps) =>
                "nav-item" + (isActive ? " is-active" : "")
              }
            >
              <div className="nav-label">{it.label}</div>
              <div className="nav-hint">{it.hint}</div>
            </NavLink>
          ))}
        </nav>
      </ContentContainer>

      <style>{`
        .nav{ padding: var(--s-5) 0; display:flex; flex-direction:column; gap: var(--s-2); }
        .nav-item{
          display:block;
          padding: 12px 12px;
          border-radius: var(--r-md);
          border: 1px solid transparent;
          color: var(--text);
          background: transparent;
          text-decoration: none;
        }
        .nav-item:hover{
          border-color: var(--border);
          background: color-mix(in srgb, var(--panel-2) 65%, black);
        }
        .nav-item.is-active{
          border-color: color-mix(in srgb, var(--accent) 55%, var(--border));
          background: color-mix(in srgb, var(--panel-2) 78%, black);
        }
        .nav-label{ font-weight: 600; }
        .nav-hint{ font-size: var(--font-sm); color: var(--muted); margin-top: 2px; }
      `}</style>
    </aside>
  );
}