import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useApi } from "../../api/ApiProvider";
import { toChartUnixSeconds } from "../../shared/time/timeDisplay";
import Papa from "papaparse";
import {
  createChart,
  CandlestickSeries,
  createSeriesMarkers,
  LineSeries,
} from "lightweight-charts";

function parseCSV(text: string) {
  const result = Papa.parse(text, {
    header: true,
    skipEmptyLines: true,
  });

  return result.data as Record<string, any>[];
}

function buildFlatLineData(
  bars: any[],
  value: number
): { time: any; value: number }[] {
  return bars
    .map((bar) => {
      const time = toChartUnixSeconds(bar.timestamp);
      if (time === null) return null;

      return {
        time: time as any,
        value,
      };
    })
    .filter((item): item is { time: any; value: number } => item !== null);
}

export function RootChartsPage() {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const { toolId, fingerprint } = useParams();
  const { http } = useApi();

  const [bars, setBars] = useState<any[]>([]);
  const [breakouts, setBreakouts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      if (!toolId || !fingerprint) {
        setError("Missing route parameters.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const manifestResponse = await http.get<any>(
          `/manifests/${toolId}/${fingerprint}`
        );

        const outputs = manifestResponse?.manifest?.outputs ?? [];

        const inputOutput = outputs.find((o: any) =>
          o.relpath?.includes("root_input_dataset")
        );

        const resultOutput = outputs.find((o: any) =>
          o.relpath?.includes("root_output_dataset")
        );

        if (!inputOutput || !resultOutput) {
          throw new Error("Required outputs not found in manifest.");
        }

        const [inputCsv, outputCsv] = await Promise.all([
          http.get<string>(
            `/artifacts/${toolId}/${fingerprint}/${inputOutput.relpath}`
          ),
          http.get<string>(
            `/artifacts/${toolId}/${fingerprint}/${resultOutput.relpath}`
          ),
        ]);

        setBars(parseCSV(inputCsv));
        setBreakouts(parseCSV(outputCsv));
      } catch (err: any) {
        setError(err?.message ?? "Failed to load root data.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [toolId, fingerprint, http]);

  useEffect(() => {
    if (!chartContainerRef.current || bars.length === 0) {
      return;
    }

    const container = chartContainerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth || 1200,
      height: container.clientHeight || 820,
      layout: {
        background: { color: "#0b0f17" },
        textColor: "#d1d5db",
      },
      grid: {
        vertLines: { color: "#1f2937" },
        horzLines: { color: "#1f2937" },
      },
      rightPriceScale: {
        borderColor: "#374151",
      },
      timeScale: {
        borderColor: "#374151",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries);

    const candleData = bars
      .map((bar) => {
        const time = toChartUnixSeconds(bar.timestamp);
        if (time === null) return null;

        return {
          time: time as any,
          open: Number(bar.open),
          high: Number(bar.high),
          low: Number(bar.low),
          close: Number(bar.close),
        };
      })
      .filter(
        (
          item
        ): item is {
          time: any;
          open: number;
          high: number;
          low: number;
          close: number;
        } => item !== null
      );

    candleSeries.setData(candleData);

    const timeToIndex = new Map<number, number>();

    bars.forEach((bar, index) => {
      const time = toChartUnixSeconds(bar.timestamp);
      if (time !== null) {
        timeToIndex.set(time, index);
      }
    });

    const balanceMap = new Map<
      string,
      {
        high: number;
        low: number;
        breakoutTime: number;
      }
    >();

    for (const breakout of breakouts) {
      const balanceId = String(breakout.parent_balance_id ?? "").trim();
      const high = Number(breakout.balance_high);
      const low = Number(breakout.balance_low);
      const rawTime = breakout.breakout_time;

      if (!balanceId || !rawTime) continue;
      if (!Number.isFinite(high) || !Number.isFinite(low)) continue;

      const breakoutTime = toChartUnixSeconds(rawTime);
      if (breakoutTime === null) continue;

      if (!balanceMap.has(balanceId)) {
        balanceMap.set(balanceId, {
          high,
          low,
          breakoutTime,
        });
      }
    }

    for (const [, balance] of balanceMap) {
      const breakoutIndex = timeToIndex.get(balance.breakoutTime);
      if (breakoutIndex === undefined) continue;

      const startIndex = Math.max(0, breakoutIndex - 5);
      const segment = bars.slice(startIndex, breakoutIndex + 1);

      const highSeries = chart.addSeries(LineSeries, {
        color: "rgba(59, 130, 246, 0.8)",
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      const lowSeries = chart.addSeries(LineSeries, {
        color: "rgba(59, 130, 246, 0.8)",
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      const midpointSeries = chart.addSeries(LineSeries, {
        color: "rgba(96, 165, 250, 0.45)",
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      highSeries.setData(buildFlatLineData(segment, balance.high));
      lowSeries.setData(buildFlatLineData(segment, balance.low));
      midpointSeries.setData(
        buildFlatLineData(segment, (balance.high + balance.low) / 2)
      );
    }

    const breakoutMarkers = breakouts
      .filter((b) => b.breakout_price && b.direction)
      .map((b) => {
        const isFailed = String(b.is_failed).trim() === "True";
        const direction = String(b.direction).trim().toLowerCase();
        const rawTime = b.breakout_time ?? b.timestamp ?? null;

        if (!rawTime) return null;

        const time = toChartUnixSeconds(rawTime);
        if (time === null) return null;

        return {
          time: time as any,
          position: direction === "up" ? "belowBar" : "aboveBar",
          color: isFailed
            ? "#f59e0b"
            : direction === "up"
            ? "#22c55e"
            : "#ef4444",
          shape: isFailed
            ? "circle"
            : direction === "up"
            ? "arrowUp"
            : "arrowDown",
          text: isFailed ? "F" : direction === "up" ? "▲" : "▼",
        };
      })
      .filter(Boolean) as any[];

    createSeriesMarkers(candleSeries, breakoutMarkers);

    chart.timeScale().fitContent();

    if (bars.length > 300) {
      chart.timeScale().setVisibleLogicalRange({
        from: bars.length - 300,
        to: bars.length,
      });
    }

    const handleResize = () => {
      chart.applyOptions({
        width: container.clientWidth || 1200,
        height: container.clientHeight || 820,
      });
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [bars, breakouts]);

  if (loading) {
    return <div style={{ padding: 24 }}>Loading root chart data...</div>;
  }

  if (error) {
    return <div style={{ padding: 24, color: "red" }}>Error: {error}</div>;
  }

  return (
    <div
      style={{
        width: "100%",
        minHeight: "calc(100vh - 150px)",
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 16,
          padding: 16,
          background: "rgba(255,255,255,0.02)",
          width: "100%",
          minHeight: "calc(100vh - 150px)",
          boxSizing: "border-box",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 14,
            flexWrap: "wrap",
            gap: 16,
          }}
        >
          <div>
            <h2 style={{ margin: 0 }}>Candlestick Chart</h2>
            <p style={{ margin: "6px 0 0 0", opacity: 0.7 }}>
              Market structure + breakout overlays
            </p>
          </div>

          <div
            style={{
              display: "flex",
              gap: 14,
              flexWrap: "wrap",
              fontSize: 13,
              opacity: 0.8,
              alignItems: "center",
            }}
          >
            {fingerprint && (
              <span style={{ opacity: 0.6 }}>
                Run: {fingerprint.slice(0, 10)}
              </span>
            )}

            <span>Total: {bars.length}</span>
            <span>BO: {breakouts.length}</span>
            <span>
              F:{" "}
              {
                breakouts.filter(
                  (b) => String(b.is_failed).trim() === "True"
                ).length
              }
            </span>
            <span>
              S:{" "}
              {
                breakouts.filter(
                  (b) => String(b.is_failed).trim() !== "True"
                ).length
              }
            </span>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            gap: 18,
            marginBottom: 14,
            flexWrap: "wrap",
            fontSize: 14,
            opacity: 0.8,
          }}
        >
          <span>🟢 ▲ Breakout UP</span>
          <span>🔴 ▼ Breakout DOWN</span>
          <span>🟠 ● Fake breakout</span>
          <span>🔵 Balance range</span>
          <span>🔷 Balance midpoint</span>
        </div>

        <div
          ref={chartContainerRef}
          style={{
            width: "100%",
            height: "calc(100vh - 240px)",
            minHeight: 820,
            borderRadius: 12,
            overflow: "hidden",
          }}
        />
      </div>
    </div>
  );
}