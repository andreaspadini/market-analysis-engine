import React from "react";
import { ToastViewport, type ToastItem, type ToastVariant } from "../../components/ui/Toast";

type ToastContextValue = {
  push: (t: { title: string; description?: string; variant?: ToastVariant; durationMs?: number }) => void;
  remove: (id: string) => void;
};

const ToastContext = React.createContext<ToastContextValue | null>(null);

function uid() {
  return Math.random().toString(16).slice(2) + "-" + Date.now().toString(16);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<ToastItem[]>([]);

  const remove = React.useCallback((id: string) => {
    setItems(prev => prev.filter(x => x.id !== id));
  }, []);

  const push: ToastContextValue["push"] = React.useCallback((t) => {
    const id = uid();
    const durationMs = t.durationMs ?? 3500;
    setItems(prev => [...prev, { id, title: t.title, description: t.description, variant: t.variant ?? "info" }]);
    window.setTimeout(() => remove(id), durationMs);
  }, [remove]);

  const value = React.useMemo(() => ({ push, remove }), [push, remove]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport items={items} onDismiss={remove} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
