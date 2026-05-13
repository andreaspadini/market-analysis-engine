import React from "react";
import { useApi } from "../api/ApiProvider";
import { PageShell } from "../app/layout/PageShell";
import { createWorkspaceClient } from "../features/workspace/api/workspaceClient";
import type {
  ArtifactRefInput,
  PatternRunRequest,
  WorkspaceStatus,
} from "../features/workspace/model/workspaceTypes";
import { ArtifactRefBadge } from "../features/workspace/components/ArtifactRefBadge";
import { StepStatusBanner } from "../features/workspace/components/StepStatusBanner";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "../components/ui/Card";
import { Collapsible } from "../components/ui/Collapsible";
import { Stack } from "../components/layout/Stack";
import { Grid } from "../components/layout/Grid";
import { Button } from "../components/ui/Button";
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  createSeriesMarkers,
} from "lightweight-charts";

type PatternToolState = {
  loading: boolean;
  error: string | null;
  lastRunId: string | null;
  artifactRef: ArtifactRefInput | null;
  status: WorkspaceStatus;
};

type PatternMatchRow = {
  pattern_id: string;
  instrument: string;
  timeframe: string;
  start_ts: string;
  end_ts: string;
  similarity_score: number;
  engine_version: string;
  run_id: string;
};
type PatternOhlcRow = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  delta?: number;
};

type PatternFilters = {
  startFrom: string;
  startTo: string;
  startTimeFrom: string;
  startTimeTo: string;
  minSimilarity: string;
};

type PatternSortField = "similarity_score" | "start_ts";
type PatternSortDirection = "asc" | "desc";

type ManualDirection = "bullish" | "bearish" | "neutral" | "any";
type ManualClosePosition = "near_high" | "near_low" | "mid" | "any";

type PatternMode =
  | "manual_template"
  | "historical_reference";



type ManualCandle = {
  index: number;
  direction: ManualDirection;
  body_ticks: number;
  upper_wick_ticks: number;
  lower_wick_ticks: number;
  volume: number;
  delta: number;
  close_position: ManualClosePosition;
};

export function PatternToolPage() {
  const { o6 } = useApi();
  const workspaceClient = React.useMemo(() => createWorkspaceClient(o6), [o6]);

  const [instrument, setInstrument] = React.useState("MNQ");
  const [timeframe, setTimeframe] = React.useState("1m");
  const [patternMode, setPatternMode] =
    React.useState<PatternMode>("manual_template");
  const [startDate, setStartDate] = React.useState("");
  const [endDate, setEndDate] = React.useState("");

  const [tickSize, setTickSize] = React.useState(0.25);
  const [bodyTicksPct, setBodyTicksPct] = React.useState(0.5);
  const [wickTicksPct, setWickTicksPct] = React.useState(1.0);
  const [volumePct, setVolumePct] = React.useState(1.0);
  const [deltaPct, setDeltaPct] = React.useState(1.0);

  const [contextBeforeBars, setContextBeforeBars] = React.useState(20);
  const [contextAfterBars, setContextAfterBars] = React.useState(40);

  const [manualCandles, setManualCandles] = React.useState<ManualCandle[]>([
    {
      index: 1,
      direction: "bullish",
      body_ticks: 10,
      upper_wick_ticks: 2,
      lower_wick_ticks: 4,
      volume: 1200,
      delta: 300,
      close_position: "near_high",
    },
    {
      index: 2,
      direction: "bearish",
      body_ticks: 8,
      upper_wick_ticks: 3,
      lower_wick_ticks: 2,
      volume: 900,
      delta: -150,
      close_position: "near_low",
    },
  ]);

  const fieldStyle: React.CSSProperties = {
    width: "100%",
    padding: "8px 10px",
    borderRadius: 10,
    border: "1px solid var(--border)",
    background: "rgba(15, 23, 42, 0.65)",
    color: "inherit",
  };

  const compactFieldStyle: React.CSSProperties = {
    width: "100%",
    padding: "4px 8px",
    borderRadius: 8,
    border: "1px solid var(--border)",
    background: "rgba(15, 23, 42, 0.65)",
    color: "inherit",
    height: 28,
    fontSize: 11,
  };

  const stepButtonStyle: React.CSSProperties = {
    height: 28,
    padding: 0,
    borderRadius: 7,
    border: "1px solid var(--border)",
    background: "rgba(15, 23, 42, 0.8)",
    color: "inherit",
    fontSize: 11,
  };

  function normalizeManualCandlesLength(nextLength: number) {
    const safeLength = Math.max(1, Math.floor(nextLength || 1));

    setManualCandles((current) => {
      const next = [...current];

      while (next.length < safeLength) {
        const last = next[next.length - 1];

        next.push({
          ...(last ?? {
            index: 1,
            direction: "bullish",
            body_ticks: 10,
            upper_wick_ticks: 2,
            lower_wick_ticks: 4,
            volume: 1200,
            delta: 300,
            close_position: "near_high",
          }),
          index: next.length + 1,
        });
      }

      return next.slice(0, safeLength).map((candle, idx) => ({
        ...candle,
        index: idx + 1,
      }));
    });
  }

  function updateManualCandle(index: number, patch: Partial<ManualCandle>) {
    setManualCandles((current) =>
      current.map((candle, idx) =>
        idx === index
          ? {
              ...candle,
              ...patch,
              index: idx + 1,
            }
          : candle
      )
    );
  }

  function stepManualCandle(index: number, key: keyof ManualCandle, delta: number) {
    setManualCandles((current) =>
      current.map((candle, idx) => {
        if (idx !== index) return candle;

        const currentValue = candle[key];

        if (typeof currentValue !== "number") return candle;

        const nextValue =
          key === "delta"
            ? currentValue + delta
            : Math.max(0, currentValue + delta);

        return {
          ...candle,
          [key]: nextValue,
        };
      })
    );
  }

  const [currentPage, setCurrentPage] = React.useState(1);

  const [manifestOutputs, setManifestOutputs] = React.useState<string[]>([]);
  const [manifestLoading, setManifestLoading] = React.useState(false);
  const [manifestError, setManifestError] = React.useState<string | null>(null);
  const [matchesCsvText, setMatchesCsvText] = React.useState<string | null>(null);
  const [matchesLoading, setMatchesLoading] = React.useState(false);
  const [matchesError, setMatchesError] = React.useState<string | null>(null);
  const [ohlcCsvText, setOhlcCsvText] = React.useState<string | null>(null);
  const [ohlcLoading, setOhlcLoading] = React.useState(false);
  const [ohlcError, setOhlcError] = React.useState<string | null>(null);
  const [selectedMatch, setSelectedMatch] = React.useState<PatternMatchRow | null>(null);
  const [selectedMatches, setSelectedMatches] = React.useState<PatternMatchRow[]>([]);
  const chartRef = React.useRef<HTMLDivElement | null>(null);
  const [showPatternOverlay, setShowPatternOverlay] = React.useState(false);
  const [showOverlayDirection, setShowOverlayDirection] = React.useState(true);
  const [showOverlayShape, setShowOverlayShape] = React.useState(true);
  const [filters, setFilters] = React.useState<PatternFilters>({
    startFrom: "",
    startTo: "",
    startTimeFrom: "",
    startTimeTo: "",
    minSimilarity: "",
  });
  const [timeDisplayMode, setTimeDisplayMode] = React.useState<"local" | "utc">("local");

  const [sortField, setSortField] = React.useState<PatternSortField>("similarity_score");
  const [sortDirection, setSortDirection] = React.useState<PatternSortDirection>("desc");

  const [matchesRelpath, setMatchesRelpath] = React.useState<string | null>(null);
  const [ohlcRelpath, setOhlcRelpath] = React.useState<string | null>(null);

  const [rawJson, setRawJson] = React.useState("");
  const [rawError, setRawError] = React.useState<string | null>(null);

  const [state, setState] = React.useState<PatternToolState>({
    loading: false,
    error: null,
    lastRunId: null,
    artifactRef: null,
    status: "IDLE",
  });

  const isValid =
    instrument.trim() !== "" &&
    timeframe.trim() !== "" &&
    startDate.trim() !== "" &&
    endDate.trim() !== "" &&
    new Date(endDate) >= new Date(startDate);

  function buildManualTemplateConfig(): Record<string, unknown> {
    return {
      mode: "manual_template",
      tick_size: tickSize,
      length_bars: manualCandles.length,
      tolerance: {
        body_ticks_pct: bodyTicksPct,
        wick_ticks_pct: wickTicksPct,
        volume_pct: volumePct,
        delta_pct: deltaPct,
      },
      candles: manualCandles.map((candle, idx) => ({
        ...candle,
        index: idx + 1,
      })),
      visualization: {
        context_before_bars: contextBeforeBars,
        context_after_bars: contextAfterBars,
      },
    };
  }

  function buildHistoricalReferenceConfig(): Record<string, unknown> {
    return {
      mode: "historical_reference",
      pattern_engine: {
        version: "1.0",
        timeframe,
      },
      universe: {
        instruments: [instrument],
        date_range: {
          start: `${startDate}T00:00:00Z`,
          end: `${endDate}T23:59:59Z`,
        },
      },
      pattern: {
        length_bars: 20,
        normalization_mode: "pattern_mean_range",
        reference_window: {
          instrument,
          timeframe,
          start_ts: `${startDate}T09:30:00Z`,
          length_bars: 20,
        },
        feature_set: {
          price: true,
          volume: true,
          delta: true,
        },
        weights: {
          price: 1,
          volume: 1,
          delta: 1,
        },
      },
      similarity: {
        tolerance: 0.2,
        distance_caps: {
          price: 1,
          volume: 1,
          delta: 1,
        },
      },
      outcome: {
        horizon_bars: 20,
        compute_atr_multiples: true,
        targets_ticks: [10],
        stops_ticks: [10],
      },
      export: {
        output_dir: "out",
        format: "csv",
      },
    };
  }

  function buildPatternConfig(): Record<string, unknown> {
    return patternMode === "manual_template"
      ? buildManualTemplateConfig()
      : buildHistoricalReferenceConfig();
  }

  function buildPatternPayload(): PatternRunRequest {
    if (
      instrument.trim() === "" ||
      timeframe.trim() === "" ||
      startDate.trim() === "" ||
      endDate.trim() === ""
    ) {
      throw new Error("Dataset fields are required before building the payload.");
    }

    if (new Date(endDate) < new Date(startDate)) {
      throw new Error("End date must be after Start date.");
    }

    return {
      dataset: {
        instruments: [instrument],
        timeframe,
        start_date: startDate,
        end_date: endDate,
      },
      config: buildPatternConfig(),
    };
  }

  function toggleSelectedMatch(match: PatternMatchRow) {
    setSelectedMatches((current) => {
      const exists = current.some(
        (item) =>
          item.pattern_id === match.pattern_id &&
          item.start_ts === match.start_ts &&
          item.end_ts === match.end_ts
      );

      if (exists) {
        return current.filter(
          (item) =>
            !(
              item.pattern_id === match.pattern_id &&
              item.start_ts === match.start_ts &&
              item.end_ts === match.end_ts
            )
        );
      }

      return [...current, match];
    });
  }

  function downloadCsv(filename: string, rows: PatternMatchRow[]) {
    if (!rows.length) return;

    const headers = Object.keys(rows[0]);

    const csv = [
      headers.join(","),
      ...rows.map((row) =>
        headers
          .map((h) => {
            const val = (row as any)[h];
            return typeof val === "string"
              ? `"${val.replace(/"/g, '""')}"`
              : val;
          })
          .join(",")
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");

    a.href = url;
    a.download = filename;
    a.click();

    URL.revokeObjectURL(url);
  }

  React.useEffect(() => {
    try {
      const payload = buildPatternPayload();
      setRawJson(JSON.stringify(payload, null, 2));
      setRawError(null);
    } catch (error) {
      setRawJson(
        JSON.stringify(
          {
            dataset: {
              instruments: [instrument],
              timeframe,
              date_range: {
                start: startDate,
                end: endDate,
              },
            },
            config: buildPatternConfig(),
          },
          null,
          2
        )
      );
      setRawError((error as Error).message);
    }
  }, [
        instrument,
        timeframe,
        startDate,
        endDate,
        tickSize,
        bodyTicksPct,
        wickTicksPct,
        volumePct,
        deltaPct,
        contextBeforeBars,
        contextAfterBars,
        manualCandles,
        patternMode,
      ]);

  async function handleSubmit() {
    if (!isValid) {
      setState((s) => ({
        ...s,
        error: "Please complete dataset fields and ensure End date is after Start date.",
      }));
      return;
    }

    const payload = buildPatternPayload();

    setState({
      loading: true,
      error: null,
      lastRunId: null,
      artifactRef: null,
      status: "PENDING",
    });

    try {
      const response = await workspaceClient.postPatternRun(payload);

      setState({
        loading: true,
        error: null,
        lastRunId: response.run_id,
        artifactRef: response.artifact,
        status: "PENDING",
      });
    } catch (error: unknown) {
      let message = "Failed to submit pattern run";

      if (error instanceof Error && error.message) {
        message = error.message;
      } else if (
        typeof error === "object" &&
        error !== null &&
        "message" in error &&
        typeof (error as { message?: unknown }).message === "string"
      ) {
        message = (error as { message: string }).message;
      }

      setState({
        loading: false,
        error: message,
        lastRunId: null,
        artifactRef: null,
        status: "FAILED",
      });
    }
  }

  React.useEffect(() => {
    if (!state.lastRunId) return;

    let isActive = true;

    const interval = window.setInterval(async () => {
      try {
        const run = await o6.getRun(state.lastRunId as string);

        if (!isActive) return;

        if (run.status === "PENDING" || run.status === "RUNNING") {
          setState((s) => ({
            ...s,
            loading: true,
            status: run.status,
          }));
          return;
        }

        if (run.status === "SUCCEEDED") {
          setState((s) => ({
            ...s,
            loading: false,
            status: "SUCCEEDED",
          }));
          window.clearInterval(interval);
          return;
        }

        if (run.status === "FAILED") {
          setState((s) => ({
            ...s,
            loading: false,
            status: "FAILED",
          }));
          window.clearInterval(interval);
        }
      } catch {
        if (!isActive) return;

        setState((s) => ({
          ...s,
          loading: false,
          status: "NOT_FOUND",
        }));

        window.clearInterval(interval);
      }
    }, 2500);

    return () => {
      isActive = false;
      window.clearInterval(interval);
    };
  }, [state.lastRunId, o6]);

  React.useEffect(() => {
    if (state.status !== "SUCCEEDED" || !state.artifactRef) {
      setManifestOutputs([]);
      setManifestError(null);
      setManifestLoading(false);
      setMatchesRelpath(null);
      setOhlcRelpath(null);
      return;
    }

    let isActive = true;

    async function loadManifest() {
      try {
        setManifestLoading(true);
        setManifestError(null);

        const response = await workspaceClient.getArtifactManifest(
          state.artifactRef!.tool_id,
          state.artifactRef!.fingerprint
        );

        if (!isActive) return;

        const outputs: string[] =
          (response as any).manifest?.outputs
            ?.map((item: any) => item.relpath)
            .filter(Boolean) ?? [];

        setManifestOutputs(outputs);

        // 👉 QUI troviamo il matches CSV
        const matchesPath =
          outputs.find(
            (relpath: string) =>
              relpath.includes("/matches/") && relpath.endsWith(".csv")
          ) ?? null;

        setMatchesRelpath(matchesPath);

        const ohlcPath =
          outputs.find(
            (relpath: string) =>
              relpath.includes("/dataset/") &&
              relpath.includes("pattern_ohlc") &&
              relpath.endsWith(".csv")
          ) ?? null;

        setOhlcRelpath(ohlcPath);
      } catch (error) {
        if (!isActive) return;

        let message = "Failed to load pattern artifact manifest";

        if (error instanceof Error && error.message) {
          message = error.message;
        }

        setManifestError(message);
        setManifestOutputs([]);
        setMatchesRelpath(null);
        setOhlcRelpath(null);
      } finally {
        if (isActive) {
          setManifestLoading(false);
        }
      }
    }

    loadManifest();

    return () => {
      isActive = false;
    };
  }, [state.status, state.artifactRef, workspaceClient]);

  React.useEffect(() => {
    if (state.status !== "SUCCEEDED" || !state.artifactRef || !matchesRelpath) {
      setMatchesCsvText(null);
      setMatchesError(null);
      setMatchesLoading(false);
      setCurrentPage(1);
      setSelectedMatch(null);
      setSelectedMatches([]);
      return;
    }

    let isActive = true;

    async function loadMatchesCsv() {
      try {
        setMatchesLoading(true);
        setMatchesError(null);

        const response = await fetch(
          `http://localhost:8000/artifacts/${encodeURIComponent(
            state.artifactRef!.tool_id
          )}/${encodeURIComponent(state.artifactRef!.fingerprint)}/${matchesRelpath}`
        );

        if (!response.ok) {
          throw new Error(`Failed to load matches CSV (${response.status})`);
        }

        const text = await response.text();

        if (!isActive) return;

        setMatchesCsvText(text);
        setCurrentPage(1);
      } catch (error) {
        if (!isActive) return;

        let message = "Failed to load matches CSV";

        if (error instanceof Error && error.message) {
          message = error.message;
        }

        setMatchesError(message);
        setMatchesCsvText(null);
      } finally {
        if (isActive) {
          setMatchesLoading(false);
        }
      }
    }

    loadMatchesCsv();

    return () => {
      isActive = false;
    };
  }, [state.status, state.artifactRef, matchesRelpath]);

  React.useEffect(() => {
    if (state.status !== "SUCCEEDED" || !state.artifactRef || !ohlcRelpath) {
      setOhlcCsvText(null);
      setOhlcError(null);
      setOhlcLoading(false);
      return;
    }

    let isActive = true;

    async function loadOhlcCsv() {
      try {
        setOhlcLoading(true);
        setOhlcError(null);

        const response = await fetch(
          `http://localhost:8000/artifacts/${encodeURIComponent(
            state.artifactRef!.tool_id
          )}/${encodeURIComponent(state.artifactRef!.fingerprint)}/${ohlcRelpath}`
        );

        if (!response.ok) {
          throw new Error(`Failed to load OHLC CSV (${response.status})`);
        }

        const text = await response.text();

        if (!isActive) return;

        setOhlcCsvText(text);
      } catch (error) {
        if (!isActive) return;

        let message = "Failed to load OHLC CSV";

        if (error instanceof Error && error.message) {
          message = error.message;
        }

        setOhlcError(message);
        setOhlcCsvText(null);
      } finally {
        if (isActive) {
          setOhlcLoading(false);
        }
      }
    }

    loadOhlcCsv();

    return () => {
      isActive = false;
    };
  }, [state.status, state.artifactRef, ohlcRelpath]);


  const parsedMatches = React.useMemo<PatternMatchRow[]>(() => {
    if (!matchesCsvText || !matchesCsvText.trim()) {
      return [];
    }

    const lines = matchesCsvText.trim().split(/\r?\n/);
    if (lines.length < 2) {
      return [];
    }

    const headers = lines[0].split(",");

    function getIndex(name: string) {
      return headers.indexOf(name);
    }

    const patternIdIndex = getIndex("pattern_id");
    const instrumentIndex = getIndex("instrument");
    const timeframeIndex = getIndex("timeframe");
    const startTsIndex = getIndex("start_ts");
    const endTsIndex = getIndex("end_ts");
    const similarityIndex = getIndex("similarity_score");
    const engineVersionIndex = getIndex("engine_version");
    const runIdIndex = getIndex("run_id");

    return lines
      .slice(1)
      .map((line) => line.split(","))
      .filter((cols) => cols.length >= headers.length)
      .map((cols) => ({
        pattern_id: cols[patternIdIndex] ?? "",
        instrument: cols[instrumentIndex] ?? "",
        timeframe: cols[timeframeIndex] ?? "",
        start_ts: cols[startTsIndex] ?? "",
        end_ts: cols[endTsIndex] ?? "",
        similarity_score: Number(cols[similarityIndex] ?? 0),
        engine_version: cols[engineVersionIndex] ?? "",
        run_id: cols[runIdIndex] ?? "",
      }));
  }, [matchesCsvText]);

  const parsedOhlc = React.useMemo<PatternOhlcRow[]>(() => {
    if (!ohlcCsvText || !ohlcCsvText.trim()) {
      return [];
    }

    const lines = ohlcCsvText.trim().split(/\r?\n/);
    if (lines.length < 2) {
      return [];
    }

    const headers = lines[0].split(",");

    function getIndex(name: string) {
      return headers.indexOf(name);
    }

    const timestampIndex = getIndex("timestamp");
    const openIndex = getIndex("open");
    const highIndex = getIndex("high");
    const lowIndex = getIndex("low");
    const closeIndex = getIndex("close");
    const volumeIndex = getIndex("volume");
    const deltaIndex = getIndex("delta");

    return lines
      .slice(1)
      .map((line) => line.split(","))
      .filter((cols) => cols.length >= 6)
      .map((cols) => ({
        timestamp: cols[timestampIndex] ?? "",
        open: Number(cols[openIndex] ?? 0),
        high: Number(cols[highIndex] ?? 0),
        low: Number(cols[lowIndex] ?? 0),
        close: Number(cols[closeIndex] ?? 0),
        volume: Number(cols[volumeIndex] ?? 0),
        delta:
          deltaIndex >= 0 && cols[deltaIndex] !== undefined && cols[deltaIndex] !== ""
            ? Number(cols[deltaIndex])
            : undefined,
      }))
      .filter((row) => row.timestamp !== "");
  }, [ohlcCsvText]);

  function formatDisplayDateTime(value: string) {
    if (!value) return "";

    if (timeDisplayMode === "utc") {
      return value.replace("T", " ").replace("+00:00", " UTC");
    }

    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;

    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }

  function extractTimeForFilter(value: string) {
    if (!value) return "";

    if (timeDisplayMode === "utc") {
      return value.slice(11, 16);
    }

    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return "";

    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");

    return `${hh}:${mm}`;
  }

  const selectedMatchWindow = React.useMemo(() => {
    if (!selectedMatch || parsedOhlc.length === 0) {
      return [];
    }

    const matchStart = new Date(selectedMatch.start_ts).getTime();
    const matchEnd = new Date(selectedMatch.end_ts).getTime();

    const matchIndexes = parsedOhlc
      .map((bar, index) => ({ bar, index }))
      .filter(({ bar }) => {
        const ts = new Date(bar.timestamp).getTime();
        return ts >= matchStart && ts <= matchEnd;
      });

    if (matchIndexes.length === 0) {
      return [];
    }

    const firstIndex = matchIndexes[0].index;
    const lastIndex = matchIndexes[matchIndexes.length - 1].index;

    const contextBefore = contextBeforeBars;
    const contextAfter = contextAfterBars;

    const windowStart = Math.max(0, firstIndex - contextBefore);
    const windowEnd = Math.min(parsedOhlc.length, lastIndex + contextAfter + 1);

    return parsedOhlc.slice(windowStart, windowEnd);
  }, [selectedMatch, parsedOhlc, contextBeforeBars, contextAfterBars]);

  const selectedMatchRange = React.useMemo(() => {
    if (!selectedMatch) {
      return null;
    }

    return {
      startTs: selectedMatch.start_ts,
      endTs: selectedMatch.end_ts,
    };
  }, [selectedMatch]);

  function buildPatternCandles() {
    const base = 100; // livello arbitrario
    let current = base;

    return manualCandles.map((candle) => {
      const body = candle.body_ticks;
      const upper = candle.upper_wick_ticks;
      const lower = candle.lower_wick_ticks;

      let open = current;
      let close =
        candle.direction === "bullish"
          ? open + body
          : candle.direction === "bearish"
            ? open - body
            : open;

      const high = Math.max(open, close) + upper;
      const low = Math.min(open, close) - lower;

      current = close;

      return { open, high, low, close };
    });
  }

  React.useEffect(() => {
    if (!chartRef.current || !selectedMatch || selectedMatchWindow.length === 0) {
      return;
    }

    const container = chartRef.current;

    const chart = createChart(container, {
      width: container.clientWidth || 800,
      height: 420,
      layout: {
        background: { color: "#0b0f17" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "rgba(31, 41, 55, 0.35)" },
        horzLines: { color: "rgba(31, 41, 55, 0.35)" },
      },
      rightPriceScale: {
        borderColor: "rgba(55, 65, 81, 0.5)",
      },
      timeScale: {
        borderColor: "rgba(55, 65, 81, 0.5)",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      priceLineVisible: false,
      lastValueVisible: false,
    });

    const data = selectedMatchWindow.map((bar) => ({
      time: Math.floor(new Date(bar.timestamp).getTime() / 1000) as any,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));

    candleSeries.setData(data);

    const matchStart = new Date(selectedMatch.start_ts).getTime();
    const matchEnd = new Date(selectedMatch.end_ts).getTime();

    const highlightData = selectedMatchWindow
      .map((bar) => {
        const ts = new Date(bar.timestamp).getTime();

        if (ts >= matchStart && ts <= matchEnd) {
          return {
            time: Math.floor(ts / 1000) as any,
            value: bar.close,
          };
        }

        return null;
      })
      .filter((v): v is { time: any; value: number } => v !== null);

    const highlightSeries = chart.addSeries(LineSeries, {
      color: "rgba(59, 130, 246, 0.75)",
      lineWidth: 3,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    highlightSeries.setData(highlightData as any);

    // ================= MANUAL TEMPLATE CANDLE OVERLAY =================
    const pattern = buildPatternCandles();

    const matchPrices = selectedMatchWindow.flatMap((bar) => [
      bar.open,
      bar.high,
      bar.low,
      bar.close,
    ]);

    const matchMax = Math.max(...matchPrices);
    const matchMin = Math.min(...matchPrices);
    const matchRange = Math.max(1, matchMax - matchMin);

    const patternPrices = pattern.flatMap((p) => [
      p.open,
      p.high,
      p.low,
      p.close,
    ]);

    const patternMin = Math.min(...patternPrices);
    const patternMax = Math.max(...patternPrices);
    const patternRange = Math.max(1, patternMax - patternMin);

    const scale = (matchRange * 0.28) / patternRange;
    const offset = matchMax + matchRange * 0.01;

    const matchBars = selectedMatchWindow
      .filter((bar) => {
        const ts = new Date(bar.timestamp).getTime();
        return ts >= matchStart && ts <= matchEnd;
      })
      .slice(0, pattern.length);

    const overlayData = matchBars.map((bar, i) => {
      const time = Math.floor(new Date(bar.timestamp).getTime() / 1000) as any;
      const p = pattern[i];

      return {
        time,
        open: offset + (p.open - patternMin) * scale,
        high: offset + (p.high - patternMin) * scale,
        low: offset + (p.low - patternMin) * scale,
        close: offset + (p.close - patternMin) * scale,
      };
    });

    if (showPatternOverlay && overlayData.length > 0) {
      const overlaySeries = chart.addSeries(CandlestickSeries, {
        upColor: "rgba(34,197,94,0.35)",
        downColor: "rgba(239,68,68,0.35)",
        borderUpColor: "rgba(34,197,94,0.95)",
        borderDownColor: "rgba(239,68,68,0.95)",
        wickUpColor: "rgba(34,197,94,0.95)",
        wickDownColor: "rgba(239,68,68,0.95)",
        priceLineVisible: false,
        lastValueVisible: false,
      });

      overlaySeries.setData(overlayData as any);
    }

    const markers = selectedMatchWindow
      .map((bar) => {
        const ts = new Date(bar.timestamp).getTime();
        const time = Math.floor(ts / 1000) as any;

        if (ts === matchStart) {
          return {
            time,
            position: "belowBar" as const,
            color: "#3b82f6",
            shape: "arrowUp" as const,
            text: "S",
          };
        }

        if (ts === matchEnd) {
          return {
            time,
            position: "aboveBar" as const,
            color: "#ef4444",
            shape: "arrowDown" as const,
            text: "E",
          };
        }

        return null;
      })
      .filter(Boolean) as any[];

    const templateMarkers =
      showPatternOverlay && (showOverlayShape || showOverlayDirection)
        ? matchBars.map((bar, overlayIndex) => {
            const candle = manualCandles[overlayIndex];
            const time = Math.floor(new Date(bar.timestamp).getTime() / 1000) as any;

            const directionColor =
              candle.direction === "bullish"
                ? "rgba(34, 197, 94, 0.9)"
                : candle.direction === "bearish"
                  ? "rgba(239, 68, 68, 0.9)"
                  : "rgba(59, 130, 246, 0.8)";

            return {
              time,
              position: "aboveBar" as const,
              color: showOverlayDirection
                ? directionColor
                : "rgba(0, 200, 255, 0.75)",
              shape: "circle" as const,
              text: showOverlayShape ? String(overlayIndex + 1) : "",
            };
          })
        : [];

    createSeriesMarkers(candleSeries, [...markers, ...templateMarkers]);

    chart.timeScale().fitContent();

    const handleResize = () => {
      chart.applyOptions({
        width: container.clientWidth || 800,
        height: 420,
      });
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [
    selectedMatch,
    selectedMatchWindow,
    showPatternOverlay,
    showOverlayDirection,
    showOverlayShape,
    manualCandles,
  ]);

  const topMatches = React.useMemo(() => {
    return [...parsedMatches]
      .sort((a, b) => b.similarity_score - a.similarity_score)
      .slice(0, 10);
  }, [parsedMatches]);

  

  const filteredMatches = React.useMemo(() => {
    

    return parsedMatches.filter((m) => {
      const matchStartDate = new Date(m.start_ts);
      const matchStartTime = extractTimeForFilter(m.start_ts);

      if (filters.startFrom && matchStartDate < new Date(filters.startFrom)) {
        return false;
      }

      if (filters.startTo) {
        const endOfDay = new Date(`${filters.startTo}T23:59:59`);
        if (matchStartDate > endOfDay) {
          return false;
        }
      }

      if (filters.startTimeFrom && matchStartTime < filters.startTimeFrom) {
        return false;
      }

      if (filters.startTimeTo && matchStartTime > filters.startTimeTo) {
        return false;
      }

      if (filters.minSimilarity && m.similarity_score < Number(filters.minSimilarity)) {
        return false;
      }

      return true;
    });
  }, [parsedMatches, filters, sortField, sortDirection, timeDisplayMode]);

  const sortedMatches = React.useMemo(() => {
    const sorted = [...filteredMatches];

    sorted.sort((a, b) => {
      if (sortField === "similarity_score") {
        return sortDirection === "asc"
          ? a.similarity_score - b.similarity_score
          : b.similarity_score - a.similarity_score;
      }

      if (sortField === "start_ts") {
        const ta = new Date(a.start_ts).getTime();
        const tb = new Date(b.start_ts).getTime();

        return sortDirection === "asc" ? ta - tb : tb - ta;
      }

      return 0;
    });

    return sorted;
  }, [filteredMatches, sortField, sortDirection]);

  const stats = React.useMemo(() => {
    if (sortedMatches.length === 0) {
      return {
        count: 0,
        avg: 0,
        min: 0,
        max: 0,
      };
    }

    const scores = sortedMatches.map((m) => m.similarity_score);

    const sum = scores.reduce((a, b) => a + b, 0);

    return {
      count: sortedMatches.length,
      avg: sum / scores.length,
      min: Math.min(...scores),
      max: Math.max(...scores),
    };
  }, [sortedMatches]);

  const pageSize = 50;

  const totalPages = Math.max(1, Math.ceil(sortedMatches.length / pageSize));

  const pagedMatches = React.useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return sortedMatches.slice(startIndex, startIndex + pageSize);
  }, [sortedMatches, currentPage]);



  return (
    <PageShell title="" description="">
      
      <Stack gap={18}>
        <Card>
          <CardHeader>
            <CardTitle>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                Configuration
                <span
                  className="subtle"
                  style={{
                    fontSize: 11,
                    opacity: 0.7,
                    letterSpacing: 0.6,
                    textTransform: "uppercase",
                  }}
                >
                  Pattern Tool
                </span>
              </div>
            </CardTitle>
          </CardHeader>

          <CardContent>
            <Stack gap={20}>
              <div className="subtle">
                Build a manual candle template, search historical matches, and inspect similarity on chart.
              </div>
              {/* ================= MODE + DATASET ================= */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "minmax(0, 1fr) 320px",
                  gap: 16,
                  alignItems: "stretch",
                }}
              >
                {/* LEFT: DATASET */}
                <div
                  style={{
                    border: "1px solid rgba(255,255,255,0.06)",
                    background: "rgba(255,255,255,0.015)",
                    borderRadius: 12,
                    padding: 14,
                  }}
                >
                  <Stack gap={14}>
                    <div>
                      <div style={{ fontWeight: 800 }}>Dataset</div>
                      <div className="subtle">
                        Select the market window where historical matches are searched.
                      </div>
                    </div>

                    <Grid columns="1fr 1fr" gap={12}>
                      <div>
                        <div className="subtle">Instrument</div>
                        <select
                          value={instrument}
                          onChange={(e) => setInstrument(e.target.value)}
                          style={fieldStyle}
                        >
                          <option value="MNQ">Micro Nasdaq (MNQ)</option>
                          <option value="NQ">Nasdaq (NQ)</option>
                          <option value="ES">S&amp;P 500 (ES)</option>
                        </select>
                      </div>

                      <div>
                        <div className="subtle">Timeframe</div>
                        <select
                          value={timeframe}
                          onChange={(e) => setTimeframe(e.target.value)}
                          style={fieldStyle}
                        >
                          <option value="1m">1 minute</option>
                          <option value="5m">5 minutes</option>
                          <option value="15m">15 minutes</option>
                        </select>
                      </div>
                    </Grid>

                    <Grid columns="1fr 1fr" gap={12}>
                      <div>
                        <div className="subtle">Start date</div>
                        <input
                          type="date"
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          style={fieldStyle}
                        />
                      </div>

                      <div>
                        <div className="subtle">End date</div>
                        <input
                          type="date"
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                          style={fieldStyle}
                        />
                      </div>
                    </Grid>
                  </Stack>
                </div>

                {/* RIGHT: MODE */}
                <div
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 12,
                    padding: 14,
                    opacity: 0.95,
                    marginTop: 4,
                    borderTop: "1px solid rgba(255,255,255,0.06)",
                    paddingTop: 14,
                  }}
                >
                  <Stack gap={12}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                      <div>
                        <div style={{ fontWeight: 800 }}>Pattern Mode</div>
                        <div className="subtle">Choose how the pattern is defined.</div>
                      </div>

                      <span
                        style={{
                          fontSize: 11,
                          padding: "3px 8px",
                          borderRadius: 999,
                          border: "1px solid var(--border)",
                          height: 22,
                        }}
                      >
                        {patternMode === "manual_template" ? "Recommended" : "Legacy"}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => setPatternMode("manual_template")}
                      style={{
                        textAlign: "left",
                        padding: 10,
                        borderRadius: 10,
                        border:
                          patternMode === "manual_template"
                            ? "2px solid rgba(34, 197, 94, 0.75)"
                            : "1px solid var(--border)",
                        background:
                          patternMode === "manual_template"
                            ? "rgba(34, 197, 94, 0.08)"
                            : "transparent",
                        color: "inherit",
                        cursor: "pointer",
                      }}
                    >
                      <div style={{ fontWeight: 700 }}>Manual Builder</div>
                      <div className="subtle">Build the candle template directly.</div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setPatternMode("historical_reference")}
                      style={{
                        textAlign: "left",
                        padding: 10,
                        borderRadius: 10,
                        border:
                          patternMode === "historical_reference"
                            ? "2px solid rgba(234, 179, 8, 0.75)"
                            : "1px solid var(--border)",
                        background:
                          patternMode === "historical_reference"
                            ? "rgba(234, 179, 8, 0.08)"
                            : "transparent",
                        color: "inherit",
                        cursor: "pointer",
                      }}
                    >
                      <div style={{ fontWeight: 700 }}>Historical Reference</div>
                      <div className="subtle">Legacy reference-window workflow.</div>
                    </button>
                  </Stack>
                </div>
              </div>

              {/* ================= MANUAL BUILDER ================= */}
              {patternMode === "manual_template" ? (
                <Stack gap={20}>
                  {/* TEMPLATE */}
                  <div
                    style={{
                      border: "1px solid rgba(34, 197, 94, 0.22)",
                      background: "rgba(34, 197, 94, 0.02)",
                      borderRadius: 12,
                      padding: 14,
                    }}
                  >
                    <Stack gap={14}>
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <div style={{ fontWeight: 800 }}>Pattern Template</div>
                          <span
                            style={{
                              fontSize: 11,
                              padding: "2px 7px",
                              borderRadius: 999,
                              background: "rgba(34, 197, 94, 0.12)",
                              border: "1px solid rgba(34, 197, 94, 0.35)",
                              fontWeight: 700,
                              opacity: 0.9,
                            }}
                          >
                            CORE
                          </span>
                        </div>
                                                <div className="subtle">
                          Define the candle sequence to search for.
                        </div>
                      </div>

                      <div>
                        <div className="subtitle">Pattern length</div>
                        <input
                          type="number"
                          min={1}
                          value={manualCandles.length}
                          onChange={(e) => normalizeManualCandlesLength(Number(e.target.value))}
                          style={{
                            ...fieldStyle,
                            width: 180,
                            fontSize: 13,
                          }}
                        />
                      </div>

                      <div style={{ display: "flex", gap: 12, overflowX: "auto", paddingBottom: 8 }}>
                        {manualCandles.map((candle, idx) => {
                          const bodyHeight = Math.max(10, Math.min(70, candle.body_ticks * 2.5));
                          const upperWickHeight = Math.max(3, Math.min(40, candle.upper_wick_ticks * 2.5));
                          const lowerWickHeight = Math.max(3, Math.min(40, candle.lower_wick_ticks * 2.5));
                          const isBullish = candle.direction === "bullish";
                          const isBearish = candle.direction === "bearish";
                          const candleColor = isBullish ? "#16a34a" : isBearish ? "#dc2626" : "#6b7280";

                          return (
                            <div
                              key={candle.index}
                              style={{
                                minWidth: 120,
                                border: "1px solid var(--border)",
                                borderRadius: 12,
                                padding: 8,
                              }}
                            >
                              <Stack gap={4}>
                                <div style={{ fontWeight: 700, fontSize: 12 }}>
                                  Candle {idx + 1}
                                </div>

                                <div
                                  style={{
                                    height: 105,
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    background: "rgba(255,255,255,0.03)",
                                    borderRadius: 10,
                                  }}
                                >
                                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                                    <div style={{ width: 2, height: upperWickHeight, background: candleColor }} />
                                    <div
                                      style={{
                                        width: 28,
                                        height: bodyHeight,
                                        borderRadius: 6,
                                        background: candle.direction === "any" ? "transparent" : candleColor,
                                        border: `2px solid ${candleColor}`,
                                      }}
                                    />
                                    <div style={{ width: 2, height: lowerWickHeight, background: candleColor }} />
                                  </div>
                                </div>

                                <div>
                                  <div className="subtle" style={{ fontSize: 10, lineHeight: "12px" }}>
                                    Direction
                                  </div>
                                  <select
                                    value={candle.direction}
                                    onChange={(e) =>
                                      updateManualCandle(idx, { direction: e.target.value as ManualDirection })
                                    }
                                    style={compactFieldStyle}
                                  >
                                    <option value="bullish">bullish</option>
                                    <option value="bearish">bearish</option>
                                    <option value="neutral">neutral</option>
                                    <option value="any">any</option>
                                  </select>
                                </div>

                                {[
                                  ["Body", "body_ticks", 1],
                                  ["Upper wick", "upper_wick_ticks", 1],
                                  ["Lower wick", "lower_wick_ticks", 1],
                                  ["Volume", "volume", 100],
                                  ["Delta", "delta", 50],
                                ].map(([label, key, step]) => (
                                  <div key={String(key)}>
                                    <div className="subtle" style={{ fontSize: 10, lineHeight: "12px" }}>
                                      {label}
                                    </div>
                                    <div style={{ display: "grid", gridTemplateColumns: "20px 1fr 20px", gap: 4 }}>
                                      <button
                                        type="button"
                                        onClick={() => stepManualCandle(idx, key as keyof ManualCandle, -Number(step))}
                                        style={stepButtonStyle}
                                      >
                                        −
                                      </button>
                                      <input
                                        type="number"
                                        value={String(candle[key as keyof ManualCandle])}
                                        onChange={(e) =>
                                          updateManualCandle(idx, {
                                            [key]: Number(e.target.value),
                                          } as Partial<ManualCandle>)
                                        }
                                        style={compactFieldStyle}
                                      />
                                      <button
                                        type="button"
                                        onClick={() => stepManualCandle(idx, key as keyof ManualCandle, Number(step))}
                                        style={stepButtonStyle}
                                      >
                                        +
                                      </button>
                                    </div>
                                  </div>
                                ))}

                                <div>
                                  <div className="subtle" style={{ fontSize: 10, lineHeight: "12px" }}>
                                    Close position
                                  </div>
                                  <select
                                    value={candle.close_position}
                                    onChange={(e) =>
                                      updateManualCandle(idx, {
                                        close_position: e.target.value as ManualClosePosition,
                                      })
                                    }
                                    style={compactFieldStyle}
                                  >
                                    <option value="near_high">near_high</option>
                                    <option value="near_low">near_low</option>
                                    <option value="mid">mid</option>
                                    <option value="any">any</option>
                                  </select>
                                </div>
                              </Stack>
                            </div>
                          );
                        })}
                      </div>
                    </Stack>
                  </div>

                  {/* SENSITIVITY + CONTEXT */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "minmax(0, 1fr) 320px",
                      gap: 16,
                      alignItems: "stretch",
                    }}
                  >
                    <div
                      style={{
                        border: "1px solid var(--border)",
                        borderRadius: 12,
                        padding: 14,
                      }}
                    >
                      <Stack gap={14}>
                        <div>
                          <div style={{ fontWeight: 800 }}>Matching Sensitivity</div>
                          <div className="subtle">
                            Control how strictly historical candles must match the template.
                          </div>
                        </div>

                        <Grid columns="1fr 1fr 1fr 1fr" gap={12}>
                          <div>
                            <div className="subtitle">Body tolerance</div>
                            <input
                              type="number"
                              step="0.1"
                              value={String(bodyTicksPct)}
                              onChange={(e) => setBodyTicksPct(Number(e.target.value))}
                              style={fieldStyle}
                            />
                          </div>

                          <div>
                            <div className="subtitle">Wick tolerance</div>
                            <input
                              type="number"
                              step="0.1"
                              value={String(wickTicksPct)}
                              onChange={(e) => setWickTicksPct(Number(e.target.value))}
                              style={fieldStyle}
                            />
                          </div>

                          <div>
                            <div className="subtitle">Volume tolerance</div>
                            <input
                              type="number"
                              step="0.1"
                              value={String(volumePct)}
                              onChange={(e) => setVolumePct(Number(e.target.value))}
                              style={fieldStyle}
                            />
                          </div>

                          <div>
                            <div className="subtitle">Delta tolerance</div>
                            <input
                              type="number"
                              step="0.1"
                              value={String(deltaPct)}
                              onChange={(e) => setDeltaPct(Number(e.target.value))}
                              style={fieldStyle}
                            />
                          </div>
                        </Grid>
                      </Stack>
                    </div>

                    <div
                      style={{
                        border: "1px solid var(--border)",
                        borderRadius: 12,
                        padding: 14,
                      }}
                    >
                      <Stack gap={12}>
                        <div>
                          <div style={{ fontWeight: 800 }}>Chart Context</div>
                          <div className="subtle">
                            Bars shown before and after each match.
                          </div>
                        </div>

                        <div>
                          <div className="subtitle">Tick size</div>
                          <input
                            type="number"
                            step="0.01"
                            value={String(tickSize)}
                            onChange={(e) => setTickSize(Number(e.target.value))}
                            style={fieldStyle}
                          />
                        </div>

                        <Grid columns="1fr 1fr" gap={8}>
                          <div>
                            <div className="subtitle">Before bars</div>
                            <input
                              type="number"
                              value={String(contextBeforeBars)}
                              onChange={(e) =>
                                setContextBeforeBars(Math.max(0, Math.floor(Number(e.target.value))))
                              }
                              style={fieldStyle}
                            />
                          </div>

                          <div>
                            <div className="subtitle">After bars</div>
                            <input
                              type="number"
                              value={String(contextAfterBars)}
                              onChange={(e) =>
                                setContextAfterBars(Math.max(0, Math.floor(Number(e.target.value))))
                              }
                              style={fieldStyle}
                            />
                          </div>
                        </Grid>
                      </Stack>
                    </div>
                  </div>
                </Stack>
              ) : (
                <div
                  style={{
                    border: "1px solid rgba(234, 179, 8, 0.35)",
                    background: "rgba(234, 179, 8, 0.04)",
                    borderRadius: 12,
                    padding: 16,
                  }}
                >
                  <Stack gap={8}>
                    <div style={{ fontWeight: 700 }}>Legacy Historical Reference Mode</div>
                    <div className="subtle">
                      This mode uses the previous historical reference-window workflow.
                      It is preserved for compatibility, regression checks, and legacy runs.
                    </div>
                    <div className="subtle">
                      Manual Builder is the recommended primary workflow.
                    </div>
                  </Stack>
                </div>
              )}

              {/* ================= ADVANCED ================= */}
              <Collapsible
                title={
                  patternMode === "manual_template"
                    ? "Preview payload — Manual Builder"
                    : "Preview payload — Legacy Historical Reference"
                }
                subtitle={
                  patternMode === "manual_template"
                    ? "Debug view of the exact Manual Builder request payload"
                    : "Debug view of the exact Legacy Historical Reference request payload"
                }
                defaultOpen={false}
                compact={true}
              >
                <Stack gap={10}>
                  <textarea
                    value={rawJson}
                    readOnly
                    rows={16}
                    style={{
                      width: "100%",
                      padding: 8,
                      borderRadius: 8,
                      fontFamily: "monospace",
                      fontSize: 12,
                    }}
                  />
                  {rawError ? <div style={{ color: "red", fontSize: 12 }}>{rawError}</div> : null}
                </Stack>
              </Collapsible>

              <StepStatusBanner
                status={state.status}
                loading={state.loading}
                error={state.error}
                lastRunId={state.lastRunId}
              />

              <div>
                <div style={{ marginBottom: 8 }}>
                  <strong>Produced pattern artifact</strong>
                </div>
                <ArtifactRefBadge artifactRef={state.artifactRef} origin="query" copyable />
              </div>
            </Stack>
          </CardContent>

          <CardFooter>
            <Button onClick={handleSubmit} disabled={!isValid || state.loading}>
              {state.loading ? "Running..." : "Run Pattern Tool"}
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Results panel</CardTitle>
          </CardHeader>

          <CardContent>
            {state.status !== "SUCCEEDED" ? (
              <div className="subtle">
                Complete a successful pattern run to load artifact-backed results.
              </div>
            ) : manifestLoading ? (
              <div className="subtle">Loading manifest outputs...</div>
            ) : manifestError ? (
              <div style={{ color: "red", fontSize: 12 }}>{manifestError}</div>
            ) : manifestOutputs.length === 0 ? (
              <div className="subtle">No manifest outputs available.</div>
            ) : matchesLoading ? (
              <div className="subtle">Loading matches CSV...</div>
            ) : matchesError ? (
              <div style={{ color: "red", fontSize: 12 }}>{matchesError}</div>
            ) : (
              <Stack gap={16}>
                <>
                {/* ================= RESULTS OVERVIEW ================= */}
                <Stack gap={16}>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: 16 }}>
                      Search results
                    </div>
                    <div className="subtle">
                      Review historical matches and inspect the selected pattern on the chart.
                    </div>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
                      gap: 12,
                    }}
                  >
                    <div className="card">
                      <div className="subtle">Matches</div>
                      <div><strong>{stats.count}</strong></div>
                    </div>

                    <div className="card">
                      <div className="subtle">Average similarity</div>
                      <div><strong>{stats.avg.toFixed(4)}</strong></div>
                    </div>

                    <div className="card">
                      <div className="subtle">Best similarity</div>
                      <div><strong>{stats.max.toFixed(4)}</strong></div>
                    </div>

                    <div className="card">
                      <div className="subtle">Lowest similarity</div>
                      <div><strong>{stats.min.toFixed(4)}</strong></div>
                    </div>
                  </div>

                  {parsedMatches.length > 0 ? (
                    <div
                      style={{
                        fontFamily: "monospace",
                        fontSize: 12,
                        padding: 8,
                        border: "1px solid var(--border)",
                        borderRadius: 8,
                      }}
                    >
                      Best match: {parsedMatches[0].pattern_id} |{" "}
                      {parsedMatches[0].start_ts} → {parsedMatches[0].end_ts} | similarity=
                      {parsedMatches[0].similarity_score.toFixed(4)}
                    </div>
                  ) : null}

                  {/* ================= FILTERS ================= */}
                  <div
                    style={{
                      border: "1px solid var(--border)",
                      borderRadius: 12,
                      padding: 12,
                    }}
                  >
                    <div style={{ fontWeight: 700, marginBottom: 8 }}>Filters</div>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "180px 1fr auto",
                        gap: 8,
                        alignItems: "end",
                      }}
                    >
                      <div>
                        <div className="subtle">Time display</div>
                        <select
                          value={timeDisplayMode}
                          onChange={(e) =>
                            setTimeDisplayMode(e.target.value as "local" | "utc")
                          }
                          style={fieldStyle}
                        >
                          <option value="local">Local</option>
                          <option value="utc">UTC</option>
                        </select>
                      </div>

                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        <input
                          type="date"
                          value={filters.startFrom}
                          onChange={(e) =>
                            setFilters((f) => ({ ...f, startFrom: e.target.value }))
                          }
                          style={{ padding: 6, borderRadius: 6 }}
                        />

                        <input
                          type="date"
                          value={filters.startTo}
                          onChange={(e) =>
                            setFilters((f) => ({ ...f, startTo: e.target.value }))
                          }
                          style={{ padding: 6, borderRadius: 6 }}
                        />

                        <input
                          type="time"
                          value={filters.startTimeFrom}
                          onChange={(e) =>
                            setFilters((f) => ({ ...f, startTimeFrom: e.target.value }))
                          }
                          style={{ padding: 6, borderRadius: 6 }}
                        />

                        <input
                          type="time"
                          value={filters.startTimeTo}
                          onChange={(e) =>
                            setFilters((f) => ({ ...f, startTimeTo: e.target.value }))
                          }
                          style={{ padding: 6, borderRadius: 6 }}
                        />

                        <input
                          type="number"
                          step="0.01"
                          value={filters.minSimilarity}
                          onChange={(e) =>
                            setFilters((f) => ({ ...f, minSimilarity: e.target.value }))
                          }
                          style={{ padding: 6, borderRadius: 6, width: 120 }}
                          placeholder="Min similarity"
                        />
                      </div>

                      <button
                        onClick={() =>
                          setFilters({
                            startFrom: "",
                            startTo: "",
                            startTimeFrom: "",
                            startTimeTo: "",
                            minSimilarity: "",
                          })
                        }
                        style={{ padding: "6px 10px", borderRadius: 6 }}
                      >
                        Reset
                      </button>
                    </div>

                    <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
                      <select
                        value={sortField}
                        onChange={(e) => setSortField(e.target.value as any)}
                      >
                        <option value="similarity_score">Similarity</option>
                        <option value="start_ts">Start time</option>
                      </select>

                      <select
                        value={sortDirection}
                        onChange={(e) => setSortDirection(e.target.value as any)}
                      >
                        <option value="desc">Descending</option>
                        <option value="asc">Ascending</option>
                      </select>

                      <Button
                        onClick={() =>
                          downloadCsv(
                            `pattern_matches_filtered_${Date.now()}.csv`,
                            sortedMatches
                          )
                        }
                        disabled={sortedMatches.length === 0}
                        variant="secondary"
                      >
                        Export filtered CSV
                      </Button>
                    </div>
                  </div>

                  {/* ================= TABLE + CHART SPLIT ================= */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "minmax(0, 0.85fr) minmax(600px, 1.65fr)",
                      gap: 16,
                      alignItems: "start",
                    }}
                  >
                    {/* LEFT: MATCH TABLE */}
                    <div
                      style={{
                        border: "1px solid var(--border)",
                        borderRadius: 12,
                        padding: 12,
                        minWidth: 0,
                      }}
                    >
                      <div style={{ marginBottom: 8 }}>
                        <div style={{ fontWeight: 800 }}>Historical matches</div>
                        <div className="subtle">
                          Select a row to inspect the matching price window.
                        </div>
                      </div>

                      <div
                        style={{
                          fontFamily: "monospace",
                          fontSize: 11,
                          padding: 6,
                          border: "1px solid var(--border)",
                          borderRadius: 8,
                          marginBottom: 8,
                        }}
                      >
                        Multi-select: {selectedMatches.length} selected
                      </div>

                      <div style={{ overflowX: "auto" }}>
                        <table
                          style={{
                            width: "max-content",
                            minWidth: "100%",
                            borderCollapse: "collapse",
                            fontSize: 12,
                          }}
                        >
                          <thead>
                            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--border)" }}>
                              <th>sel</th>
                              <th>#</th>
                              <th>instrument</th>
                              <th>timeframe</th>
                              <th>start ({timeDisplayMode})</th>
                              <th>end ({timeDisplayMode})</th>
                              <th>similarity</th>
                            </tr>
                          </thead>

                          <tbody>
                            {pagedMatches.map((m, i) => {
                              const isPrimarySelected =
                                selectedMatch?.start_ts === m.start_ts &&
                                selectedMatch?.pattern_id === m.pattern_id;

                              const isMultiSelected = selectedMatches.some(
                                (item) =>
                                  item.pattern_id === m.pattern_id &&
                                  item.start_ts === m.start_ts &&
                                  item.end_ts === m.end_ts
                              );

                              return (
                                <tr
                                  key={i}
                                  onClick={() => setSelectedMatch(m)}
                                  style={{
                                    borderBottom: "1px solid var(--border)",
                                    cursor: "pointer",
                                    background: isPrimarySelected
                                      ? "rgba(0, 120, 255, 0.25)"
                                      : isMultiSelected
                                        ? "rgba(34, 197, 94, 0.08)"
                                        : "transparent",
                                    outline: isPrimarySelected ? "1px solid rgba(0,120,255,0.5)" : "none",
                                    boxShadow: isPrimarySelected
                                      ? "inset 3px 0 0 rgba(0,120,255,0.8)"
                                      : "none",
                                  }}
                                >
                                  <td>
                                    <input
                                      type="checkbox"
                                      checked={isMultiSelected}
                                      onChange={() => toggleSelectedMatch(m)}
                                      onClick={(e) => e.stopPropagation()}
                                    />
                                  </td>
                                  <td>{(currentPage - 1) * pageSize + i + 1}</td>
                                  <td>{m.instrument}</td>
                                  <td>{m.timeframe}</td>
                                  <td title={m.start_ts}>{formatDisplayDateTime(m.start_ts)}</td>
                                  <td title={m.end_ts}>{formatDisplayDateTime(m.end_ts)}</td>
                                  <td>{m.similarity_score.toFixed(4)}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          gap: 12,
                          marginTop: 12,
                        }}
                      >
                        <Button
                          variant="secondary"
                          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                          disabled={currentPage === 1}
                        >
                          Prev
                        </Button>

                        <div className="subtle">
                          Page {currentPage} / {totalPages}
                        </div>

                        <Button
                          variant="secondary"
                          onClick={() =>
                            setCurrentPage((p) => Math.min(totalPages, p + 1))
                          }
                          disabled={currentPage === totalPages}
                        >
                          Next
                        </Button>
                      </div>
                    </div>

                    {/* RIGHT: SELECTED MATCH */}
                    <div
                      style={{
                        border: "1px solid var(--border)",
                        borderRadius: 12,
                        padding: 12,
                        minHeight: 420,
                      }}
                    >
                      <div style={{ marginBottom: 8 }}>
                        {selectedMatch ? (() => {
                          const score = selectedMatch.similarity_score;

                          const scoreColor =
                            score > 0.38
                              ? "#22c55e"
                              : score > 0.34
                                ? "#eab308"
                                : "#ef4444";

                          return (
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                              }}
                            >
                              <div>
                                <div style={{ fontWeight: 800 }}>Selected match</div>
                                <div className="subtle">
                                  {formatDisplayDateTime(selectedMatch.start_ts)} →{" "}
                                  {formatDisplayDateTime(selectedMatch.end_ts)}
                                </div>
                              </div>

                              <div style={{ textAlign: "right" }}>
                                <div className="subtle">Similarity</div>
                                <div style={{ fontWeight: 900, fontSize: 16, color: scoreColor }}>
                                  {score.toFixed(4)}
                                </div>
                              </div>
                            </div>
                          );
                        })() : (
                          <div>
                            <div style={{ fontWeight: 800 }}>Selected match</div>
                            <div className="subtle">Select a row to inspect the pattern.</div>
                          </div>
                        )}
                      </div>

                      {selectedMatch ? (
                        <div
                          style={{
                            display: "flex",
                            gap: 12,
                            alignItems: "center",
                            flexWrap: "wrap",
                            marginBottom: 10,
                            fontSize: 12,
                          }}
                        >
                          <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <input
                              type="checkbox"
                              checked={showPatternOverlay}
                              onChange={(e) => setShowPatternOverlay(e.target.checked)}
                            />
                            Show overlay
                          </label>

                          <label
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 6,
                              opacity: showPatternOverlay ? 1 : 0.45,
                            }}
                          >
                            <input
                              type="checkbox"
                              checked={showOverlayDirection}
                              disabled={!showPatternOverlay}
                              onChange={(e) => setShowOverlayDirection(e.target.checked)}
                            />
                            Direction
                          </label>

                          <label
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 6,
                              opacity: showPatternOverlay ? 1 : 0.45,
                            }}
                          >
                            <input
                              type="checkbox"
                              checked={showOverlayShape}
                              disabled={!showPatternOverlay}
                              onChange={(e) => setShowOverlayShape(e.target.checked)}
                            />
                            Shape
                          </label>
                        </div>
                      ) : null}

                      {selectedMatch ? (
                        <>
                          <div
                            style={{
                              fontSize: 12,
                              opacity: 0.7,
                              marginBottom: 8,
                            }}
                          >
                            Window: <strong>{selectedMatchWindow.length}</strong> bars
                          </div>

                          {selectedMatchWindow.length > 0 ? (
                            <div
                              ref={chartRef}
                              style={{
                                height: 420,
                                borderRadius: 6,
                              }}
                            />
                          ) : (
                            <div className="subtle">Loading selected match candles...</div>
                          )}
                        </>
                      ) : (
                        <div
                          className="subtle"
                          style={{
                            border: "1px dashed var(--border)",
                            borderRadius: 10,
                            padding: 20,
                          }}
                        >
                          Select a row to inspect the pattern.
                        </div>
                      )}
                    </div>
                  </div>
                </Stack>
              </>
              </Stack>
            )}
          </CardContent>
        </Card>
          </Stack>
        </PageShell>
      );
    }