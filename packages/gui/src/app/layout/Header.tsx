import React from "react";
import { useTheme } from "../providers/ThemeProvider";
import { Button } from "../../components/ui/Button";
import { ContentContainer } from "./ContentContainer";
import logo from "../../assets/spaditools-logo.png";

export function Header() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="app-shell__header no-print">
      <ContentContainer>
        <div className="hdr">

          {/* BRAND */}
          <div className="brand">
            <div className="logo" aria-hidden>
              <img src={logo} alt="" />
            </div>

            <div className="title">SPADITOOLS</div>
          </div>

          {/* ACTIONS */}
          <div className="actions">
            <span className="pill">Theme: {theme}</span>
            <Button variant="ghost" size="sm" onClick={toggleTheme}>
              Toggle
            </Button>
          </div>

        </div>
      </ContentContainer>

      <style>{`
        .app-shell__header{
          background: color-mix(in srgb, var(--panel) 88%, black);
          border-bottom: 1px solid var(--border);
          position: sticky;
          top: 0;
          z-index: 30;
        }

        .hdr{
          height: 64px;
          display:flex;
          align-items:center;
          justify-content:space-between;
          gap: var(--s-4);
        }

        .brand{
          display:flex;
          align-items:center;
          gap: 10px;
        }

        .logo{
          width: 36px;
          height: 36px;
          border-radius: 10px;
          overflow: hidden;
          display:flex;
          align-items:center;
          justify-content:center;
          background: rgba(255,255,255,0.04);
          border: 1px solid var(--border);
        }

        .logo img{
          width: 80%;
          height: 80%;
          object-fit: contain;
        }

        .title{
          font-size: 18px;
          font-weight: 800;
          letter-spacing: 1.2px;
        }

        .actions{
          display:flex;
          align-items:center;
          gap: var(--s-3);
        }
      `}</style>
    </header>
  );
}