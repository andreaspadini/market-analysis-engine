import { useEffect, useRef, useState } from "react";
import { useApi } from "../../api/ApiProvider";
import type { O6RunStatus } from "../../api/bindings/o6";
import type { HttpError } from "../../api/client/httpClient";

export type UiRunStatus = O6RunStatus | "NOT_FOUND";

type UseRunStatusResult = {
  status: UiRunStatus;
  isPolling: boolean;
  error?: string;
};

const POLL_MS = 2500;

function isTerminal(status: UiRunStatus) {
  return (
    status === "SUCCEEDED" ||
    status === "FAILED" ||
    status === "NOT_FOUND"
  );
}

export function useRunStatus(runId: string): UseRunStatusResult {
  const { o6 } = useApi();

  const [status, setStatus] = useState<UiRunStatus>("PENDING");
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string>();
  const intervalRef = useRef<number | null>(null);
  const cancelledRef = useRef(false);
  const inFlightRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;
console.log("useRunStatus effect", { runId, hasGetRun: typeof o6.getRun });
    const stop = () => {
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsPolling(false);
    };

    const fetchOnce = async () => {
      if (!runId || inFlightRef.current) return;
      inFlightRef.current = true;

      try {
        setError(undefined);

        const run = await o6.getRun(runId);
        if (cancelledRef.current) return;

        setStatus(run.status);

        if (isTerminal(run.status)) stop();
      } catch (e) {
        if (cancelledRef.current) return;

        const err = e as HttpError;

        if (err.status === 404) {
          setStatus("NOT_FOUND");
          stop();
          return;
        }

        setError(err.message);
      } finally {
        inFlightRef.current = false;
      }
    };

    fetchOnce();

    setIsPolling(true);
    intervalRef.current = window.setInterval(fetchOnce, POLL_MS);

    return () => {
      cancelledRef.current = true;
      if (intervalRef.current !== null) {
        window.clearInterval(intervalRef.current);
      }
    };
  }, [o6, runId]);

  return { status, isPolling, error };
}