// apps/gui-web/src/env.ts
export type GuiWebEnv = {
  O6_BASE_URL: string;
};

export function getEnv(): GuiWebEnv {
  // Minimo: niente logica, niente fallback “smart”.
  return {
    O6_BASE_URL: import.meta.env.VITE_O6_BASE_URL ?? "",
  };
}