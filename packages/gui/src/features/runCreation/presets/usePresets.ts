import * as React from "react";
import type { PresetsState, RunParameters, RunPreset } from "../types";
import { loadPresetsState, savePresetsState } from "./presetStorage";

function now(): number {
  return Date.now();
}

function newId(): string {
  return "p_" + Math.random().toString(36).slice(2, 10) + "_" + Math.random().toString(36).slice(2, 8);
}

function defaultParams(): RunParameters {
  return {
    dataset: null,
    window: null,
    mode: "basic",
    advanced: {},
  };
}

function defaultState(): PresetsState {
  const preset: RunPreset = {
    id: newId(),
    name: "Default Preset",
    createdAt: now(),
    updatedAt: now(),
    params: defaultParams(),
  };

  return {
    activePresetId: preset.id,
    presets: [preset],
  };
}

export type UsePresetsApi = {
  state: PresetsState;
  activePreset: RunPreset | null;

  setActive: (id: string) => void;

  createPreset: (name?: string) => void;
  renamePreset: (id: string, name: string) => void;
  updatePresetParams: (id: string, params: RunParameters) => void;

  duplicatePreset: (id: string) => void;
  deletePreset: (id: string) => void;

  resetToDefault: () => void;
};

export function usePresets(): UsePresetsApi {
  const [state, setState] = React.useState<PresetsState>(() => {
    const loaded = loadPresetsState();
    return loaded ?? defaultState();
  });

  React.useEffect(() => {
    savePresetsState(state);
  }, [state]);

  const activePreset: RunPreset | null =
    state.activePresetId
      ? state.presets.find((p: RunPreset) => p.id === state.activePresetId) ?? null
      : null;

  const setActive = React.useCallback((id: string) => {
    setState((prev: PresetsState) => ({ ...prev, activePresetId: id }));
  }, []);

  const createPreset = React.useCallback((name?: string) => {
    setState((prev: PresetsState) => {
      const preset: RunPreset = {
        id: newId(),
        name: name?.trim() || `Preset ${prev.presets.length + 1}`,
        createdAt: now(),
        updatedAt: now(),
        params: defaultParams(),
      };
      return {
        activePresetId: preset.id,
        presets: [preset, ...prev.presets],
      };
    });
  }, []);

  const renamePreset = React.useCallback((id: string, name: string) => {
    setState((prev: PresetsState) => ({
      ...prev,
      presets: prev.presets.map((p: RunPreset) =>
        p.id === id ? { ...p, name: name.trim() || p.name, updatedAt: now() } : p
      ),
    }));
  }, []);

  const updatePresetParams = React.useCallback((id: string, params: RunParameters) => {
    setState((prev: PresetsState) => ({
      ...prev,
      presets: prev.presets.map((p: RunPreset) => (p.id === id ? { ...p, params, updatedAt: now() } : p)),
    }));
  }, []);

  const duplicatePreset = React.useCallback((id: string) => {
    setState((prev: PresetsState) => {
      const src = prev.presets.find((p: RunPreset) => p.id === id);
      if (!src) return prev;

      const copy: RunPreset = {
        ...src,
        id: newId(),
        name: `${src.name} (copy)`,
        createdAt: now(),
        updatedAt: now(),
      };

      return {
        activePresetId: copy.id,
        presets: [copy, ...prev.presets],
      };
    });
  }, []);

  const deletePreset = React.useCallback((id: string) => {
    setState((prev: PresetsState) => {
      const nextPresets = prev.presets.filter((p: RunPreset) => p.id !== id);

      if (nextPresets.length === 0) return defaultState();

      const nextActive =
        prev.activePresetId === id ? nextPresets[0]?.id ?? null : prev.activePresetId;

      return { activePresetId: nextActive, presets: nextPresets };
    });
  }, []);

  const resetToDefault = React.useCallback(() => {
    setState(defaultState());
  }, []);

  return {
    state,
    activePreset,
    setActive,
    createPreset,
    renamePreset,
    updatePresetParams,
    duplicatePreset,
    deletePreset,
    resetToDefault,
  };
}