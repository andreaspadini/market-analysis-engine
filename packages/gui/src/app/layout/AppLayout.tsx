import React from "react";
import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { TopNavigation } from "./TopNavigation";

export function AppLayout() {
  return (
    <div className="app-shell">
      <Header />
      <TopNavigation />

      <main className="app-shell__content">
        <Outlet />
      </main>

      <style>{`
        .app-shell{
          min-height: 100vh;
          display: grid;
          grid-template-columns: 1fr;
          grid-template-rows: 64px 44px 1fr;
          grid-template-areas:
            "header"
            "topnav"
            "content";
        }

        .app-shell__header{
          grid-area: header;
        }

        .app-shell__content{
          grid-area: content;
          padding: var(--s-4) var(--s-4);
          width: 100%;
          max-width: 1600px;
          margin: 0 auto;
        }

        @media (max-width: 980px){
          .app-shell{
            grid-template-columns: 1fr;
            grid-template-rows: 64px 44px 1fr;
            grid-template-areas:
              "header"
              "topnav"
              "content";
          }

          .app-shell__content{
            padding: var(--s-4);
            width: 100%;
            max-width: 1440px;
            margin: 0 auto;
          }
        }
      `}</style>
    </div>
  );
}