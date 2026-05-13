export type RunParameters = {
  dataset: string | null;
  window: number | null;
  mode: "basic" | "advanced";
  advanced: Record<string, unknown>;
};

export type RunPreset = {
  id: string;
  name: string;
  createdAt: number;
  updatedAt: number;
  params: RunParameters;
};

export type PresetsState = {
  activePresetId: string | null;
  presets: RunPreset[];
};