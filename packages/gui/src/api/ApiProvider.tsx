import React from "react";
import { createHttpClient, type HttpClient } from "./client/httpClient";
import { createO6Client, type O6Client } from "./bindings/o6";

export type ApiContextValue = {
  http: HttpClient;
  o6: O6Client;
};

const ApiContext = React.createContext<ApiContextValue | null>(null);

export function ApiProvider(props: { baseUrl: string; children: React.ReactNode }) {
  const { baseUrl, children } = props;

  const value = React.useMemo<ApiContextValue>(() => {
    const http = createHttpClient(baseUrl);
    const o6 = createO6Client(http);
    return { http, o6 };
  }, [baseUrl]);

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
}

export function useApi(): ApiContextValue {
  const ctx = React.useContext(ApiContext);
  if (!ctx) throw new Error("useApi must be used within ApiProvider");
  return ctx;
}