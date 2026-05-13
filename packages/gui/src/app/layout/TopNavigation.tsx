import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { routes } from "../routes";

export function TopNavigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const items = [
    { label: "Workspace", path: routes.workspaceRoot },
    { label: "Pattern Tool", path: routes.patterns },
  ];

  return (
    <div className="top-nav-wrapper">
      <div className="top-nav">
        {items.map((item) => {
          const active = location.pathname.startsWith(item.path);

          return (
            <button
              key={item.path}
              type="button"
              onClick={() => navigate(item.path)}
              className={"top-nav__item" + (active ? " is-active" : "")}
            >
              {item.label}
            </button>
          );
        })}
      </div>

      <style>{`
        .top-nav-wrapper{
          grid-area: topnav;
          border-bottom: 1px solid var(--border);
          background: color-mix(in srgb, var(--panel) 92%, black);
        }

        .top-nav{
            display: flex;
            justify-content: center;
            gap: 80px;
            padding: 6px 16px;
            width: 100%;
            max-width: 1440px;
            margin: 0 auto;
            }

        .top-nav__item{
          border: 1px solid transparent;
          background: transparent;
          color: var(--text);
          padding: 6px 12px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 16px;
        }

        .top-nav__item:hover{
          background: color-mix(in srgb, var(--panel-2) 60%, black);
        }

        .top-nav__item.is-active{
          border: 1px solid var(--border);
          background: color-mix(in srgb, var(--panel-2) 80%, black);
          font-weight: 600;
        }
      `}</style>
    </div>
  );
}