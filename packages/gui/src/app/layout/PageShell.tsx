import React from "react";
import { ContentContainer } from "./ContentContainer";

export function PageShell(props: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  const { title, description, actions, children, className } = props;

  return (
    <ContentContainer>
      <div className={"page-shell " + (className ?? "")}>
        <div className="page-shell__head">
          <div className="page-shell__text">
            <div>
              {title ? (
                <div className="page-shell__title">{title}</div>
              ) : null}
              {description ? (
                <div className="page-shell__desc subtle">{description}</div>
              ) : null}
            </div>
          </div>

          {actions ? (
            <div className="page-shell__actions no-print">
              {actions}
            </div>
          ) : null}
        </div>

        <div className="page-shell__body">{children}</div>
      </div>

      <style>{`
        .page-shell{
          display:flex;
          flex-direction:column;
          gap: var(--s-4);
        }

        .page-shell__head{
          display:grid;
          grid-template-columns: 1fr auto;
          align-items:center;
          gap: var(--s-4);
          padding-top: 6px;
        }

        .page-shell__text{
          display:flex;
          justify-content:center;
          width:100%;
          text-align:center;
        }

        .page-shell__title{
          font-size: 18px;
          font-weight: 700;
          letter-spacing: .1px;
          line-height: 1.2;
        }

        .page-shell__desc{
          max-width: 720px;
          font-size: 14px;
          line-height: 1.45;
          color: var(--muted);
        }

        .page-shell__body{
          display:flex;
          flex-direction:column;
          gap: var(--s-4);
        }

        .page-shell__actions{
          justify-self:end;
        }

        @media (max-width: 980px){
          .page-shell__head{
            grid-template-columns: 1fr;
            justify-items: center;
          }

          .page-shell__actions{
            justify-self: center;
          }
        }
      `}</style>
    </ContentContainer>
  );
}