import { useEffect, useRef, useState } from "react";
import { useApi } from "../../api/ApiProvider";
import type { HttpError } from "../../api/client/httpClient";

export type ResultsSnapshot = {
  root?: unknown;
  statistical?: unknown;
  query?: unknown;
  [key: string]: unknown;
};

type UseRunResultsResult = {
  data: ResultsSnapshot | null;
  isLoading: boolean;
  error?: string;
};

export function useRunResults(
  runId: string,
  enabled: boolean
): UseRunResultsResult {
  const { o6 } = useApi();

  const [data, setData] = useState<ResultsSnapshot | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>();
  const fetchedRef = useRef(false);
  const cancelledRef = useRef(false);

  useEffect(() => {
    cancelledRef.current = false;

    if (!enabled || !runId || fetchedRef.current) {
      return () => {
        cancelledRef.current = true;
      };
    }

    const fetchResults = async () => {
      try {
        setIsLoading(true);
        setError(undefined);

        const response = await o6.getRunResults(runId);
        if (cancelledRef.current) return;

        setData((response.results ?? null) as ResultsSnapshot | null);
        fetchedRef.current = true;
      } catch (e) {
        if (cancelledRef.current) return;

        const err = e as HttpError;
        setError(err.message);
      } finally {
        if (!cancelledRef.current) {
          setIsLoading(false);
        }
      }
    };

    fetchResults();

    return () => {
      cancelledRef.current = true;
    };
  }, [enabled, o6, runId]);

  return { data, isLoading, error };
}

export default useRunResults;