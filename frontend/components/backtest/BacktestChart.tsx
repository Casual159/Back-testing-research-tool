"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  Time,
  SeriesMarker,
} from "lightweight-charts";
import { chartColors, defaultChartOptions, indicatorColors } from "@/lib/chart-theme";

// ── Types ──────────────────────────────────────────────────────────────

export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Trade {
  entry_time: string;
  entry_price: number;
  exit_time: string;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
}

export interface IndicatorData {
  time: number;
  [key: string]: number | null;
}

export type IndicatorId =
  | "sma_20" | "sma_50" | "sma_200"
  | "ema_12" | "ema_26"
  | "bb_upper" | "bb_middle" | "bb_lower"
  | "rsi"
  | "macd" | "macd_signal" | "macd_histogram";

interface BacktestChartProps {
  candles: CandleData[];
  trades: Trade[];
  playbackIndex?: number | null; // null = show all
  indicatorData?: IndicatorData[];
  enabledIndicators?: IndicatorId[];
  height?: number;
}

interface TooltipData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// ── Helpers ────────────────────────────────────────────────────────────

function isoToUnix(iso: string): number {
  return Math.floor(new Date(iso).getTime() / 1000);
}

function tradesToMarkers(
  trades: Trade[],
  visibleUpTo?: number
): SeriesMarker<Time>[] {
  const markers: SeriesMarker<Time>[] = [];

  for (const trade of trades) {
    const entryTime = isoToUnix(trade.entry_time);
    const exitTime = isoToUnix(trade.exit_time);

    if (visibleUpTo !== undefined && entryTime > visibleUpTo) continue;

    markers.push({
      time: entryTime as Time,
      position: "belowBar",
      color: "#22c55e",
      shape: "arrowUp",
      text: `BUY $${trade.entry_price.toFixed(0)}`,
      size: 1,
    });

    if (visibleUpTo === undefined || exitTime <= visibleUpTo) {
      markers.push({
        time: exitTime as Time,
        position: "aboveBar",
        color: "#ef4444",
        shape: "arrowDown",
        text: `${trade.pnl >= 0 ? "+" : ""}${trade.pnl_pct.toFixed(1)}%`,
        size: 1,
      });
    }
  }

  return markers.sort((a, b) => (a.time as number) - (b.time as number));
}

// ── Overlay indicator types (rendered on main price chart) ─────────

const OVERLAY_INDICATORS = new Set([
  "sma_20", "sma_50", "sma_200",
  "ema_12", "ema_26",
  "bb_upper", "bb_middle", "bb_lower",
]);

// ── Component ──────────────────────────────────────────────────────────

export default function BacktestChart({
  candles,
  trades,
  playbackIndex = null,
  indicatorData,
  enabledIndicators = [],
  height = 500,
}: BacktestChartProps) {
  const mainContainerRef = useRef<HTMLDivElement>(null);
  const rsiContainerRef = useRef<HTMLDivElement>(null);
  const macdContainerRef = useRef<HTMLDivElement>(null);

  const mainChartRef = useRef<IChartApi | null>(null);
  const rsiChartRef = useRef<IChartApi | null>(null);
  const macdChartRef = useRef<IChartApi | null>(null);

  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const overlaySeriesRef = useRef<Map<string, ISeriesApi<"Line">>>(new Map());
  const rsiSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdLineRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdSignalRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdHistRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  const syncingRef = useRef(false);

  const [tooltipData, setTooltipData] = useState<TooltipData | null>(null);

  // Determine which candles are visible based on playback
  const visibleCount = playbackIndex !== null ? playbackIndex + 1 : candles.length;
  const visibleCandles = candles.slice(0, visibleCount);
  const currentTime = visibleCandles.length > 0 ? visibleCandles[visibleCandles.length - 1].time : undefined;

  // ── Show RSI / MACD sub-charts? ───────────────────────────────────
  const showRsi = enabledIndicators.includes("rsi");
  const showMacd = enabledIndicators.some((i) =>
    ["macd", "macd_signal", "macd_histogram"].includes(i)
  );

  // ── Create / destroy main chart ───────────────────────────────────
  useEffect(() => {
    if (!mainContainerRef.current || candles.length === 0) return;

    const chart = createChart(mainContainerRef.current, {
      ...defaultChartOptions,
      width: mainContainerRef.current.clientWidth,
      height,
      leftPriceScale: { visible: true, borderColor: chartColors.grid },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: chartColors.upCandle,
      downColor: chartColors.downCandle,
      borderUpColor: chartColors.upCandle,
      borderDownColor: chartColors.downCandle,
      wickUpColor: chartColors.upCandle,
      wickDownColor: chartColors.downCandle,
    });

    const volumeSeries = chart.addHistogramSeries({
      color: chartColors.volumeBase,
      priceFormat: { type: "volume" },
      priceScaleId: "left",
    });

    chart.priceScale("left").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    mainChartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // Tooltip
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.point) {
        setTooltipData(null);
        return;
      }
      const candle = candles.find((c) => c.time === param.time);
      if (!candle) {
        setTooltipData(null);
        return;
      }
      const date = new Date((param.time as number) * 1000);
      setTooltipData({
        time: date.toLocaleString(),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume,
      });
    });

    // Resize handler
    const handleResize = () => {
      if (mainContainerRef.current) {
        chart.applyOptions({ width: mainContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      overlaySeriesRef.current.clear();
      chart.remove();
      mainChartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, [candles.length > 0 ? candles[0].time : 0, height]); // Re-create only when dataset changes

  // ── Update visible data (candles + volume + markers) ──────────────
  useEffect(() => {
    if (!candleSeriesRef.current || !volumeSeriesRef.current) return;

    const candleData = visibleCandles.map((c) => ({
      time: c.time as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    const volumeData = visibleCandles.map((c) => ({
      time: c.time as Time,
      value: c.volume,
      color: c.close >= c.open ? chartColors.volumeUp : chartColors.volumeDown,
    }));

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);

    // Trade markers
    const markers = tradesToMarkers(trades, currentTime);
    candleSeriesRef.current.setMarkers(markers);

    // Fit on first render only
    if (playbackIndex === null && mainChartRef.current) {
      mainChartRef.current.timeScale().fitContent();
    }
  }, [visibleCandles.length, currentTime, trades]);

  // ── Overlay indicators (SMA, EMA, BB on main chart) ───────────────
  useEffect(() => {
    const chart = mainChartRef.current;
    if (!chart || !indicatorData || indicatorData.length === 0) return;

    const enabledOverlays = enabledIndicators.filter((id) => OVERLAY_INDICATORS.has(id));

    // Remove series that are no longer enabled
    for (const [id, series] of overlaySeriesRef.current) {
      if (!enabledOverlays.includes(id as IndicatorId)) {
        chart.removeSeries(series);
        overlaySeriesRef.current.delete(id);
      }
    }

    // Add/update enabled overlay series
    for (const id of enabledOverlays) {
      let series = overlaySeriesRef.current.get(id);
      if (!series) {
        series = chart.addLineSeries({
          color: indicatorColors[id as keyof typeof indicatorColors] || "#888",
          lineWidth: id.startsWith("bb_") ? 1 : 2,
          lineStyle: id.startsWith("bb_") && id !== "bb_middle" ? 2 : 0, // dashed for bands
          priceScaleId: "right",
        });
        overlaySeriesRef.current.set(id, series);
      }

      const data = indicatorData
        .slice(0, visibleCount)
        .filter((d) => d[id] !== null && d[id] !== undefined)
        .map((d) => ({ time: d.time as Time, value: d[id] as number }));

      series.setData(data);
    }
  }, [enabledIndicators, indicatorData, visibleCount]);

  // ── RSI sub-chart ─────────────────────────────────────────────────
  useEffect(() => {
    if (!showRsi || !rsiContainerRef.current) {
      // Destroy if toggled off
      if (rsiChartRef.current) {
        rsiChartRef.current.remove();
        rsiChartRef.current = null;
        rsiSeriesRef.current = null;
      }
      return;
    }

    if (!rsiChartRef.current) {
      const chart = createChart(rsiContainerRef.current, {
        ...defaultChartOptions,
        width: rsiContainerRef.current.clientWidth,
        height: 120,
        rightPriceScale: {
          borderColor: chartColors.grid,
          scaleMargins: { top: 0.1, bottom: 0.1 },
        },
      });

      const rsiSeries = chart.addLineSeries({
        color: indicatorColors.rsi,
        lineWidth: 2,
        priceFormat: { type: "custom", formatter: (v: number) => v.toFixed(0) },
      });

      // Reference lines at 30 and 70
      rsiSeries.createPriceLine({ price: 70, color: "#ef444460", lineWidth: 1, lineStyle: 2, axisLabelVisible: true });
      rsiSeries.createPriceLine({ price: 30, color: "#22c55e60", lineWidth: 1, lineStyle: 2, axisLabelVisible: true });
      rsiSeries.createPriceLine({ price: 50, color: "#6b728040", lineWidth: 1, lineStyle: 2, axisLabelVisible: false });

      rsiChartRef.current = chart;
      rsiSeriesRef.current = rsiSeries;

      // Sync time scale with main chart
      syncTimeScales(mainChartRef.current, chart);

      // Resize
      const handleResize = () => {
        if (rsiContainerRef.current) {
          chart.applyOptions({ width: rsiContainerRef.current.clientWidth });
        }
      };
      window.addEventListener("resize", handleResize);
      return () => {
        window.removeEventListener("resize", handleResize);
      };
    }
  }, [showRsi]);

  // Update RSI data
  useEffect(() => {
    if (!rsiSeriesRef.current || !indicatorData) return;
    const data = indicatorData
      .slice(0, visibleCount)
      .filter((d) => d.rsi !== null && d.rsi !== undefined)
      .map((d) => ({ time: d.time as Time, value: d.rsi as number }));
    rsiSeriesRef.current.setData(data);
  }, [indicatorData, visibleCount, showRsi]);

  // ── MACD sub-chart ────────────────────────────────────────────────
  useEffect(() => {
    if (!showMacd || !macdContainerRef.current) {
      if (macdChartRef.current) {
        macdChartRef.current.remove();
        macdChartRef.current = null;
        macdLineRef.current = null;
        macdSignalRef.current = null;
        macdHistRef.current = null;
      }
      return;
    }

    if (!macdChartRef.current) {
      const chart = createChart(macdContainerRef.current, {
        ...defaultChartOptions,
        width: macdContainerRef.current.clientWidth,
        height: 120,
      });

      const histSeries = chart.addHistogramSeries({
        color: indicatorColors.macd_histogram_pos,
        priceFormat: { type: "custom", formatter: (v: number) => v.toFixed(2) },
      });
      const lineSeries = chart.addLineSeries({
        color: indicatorColors.macd,
        lineWidth: 2,
      });
      const signalSeries = chart.addLineSeries({
        color: indicatorColors.macd_signal,
        lineWidth: 1,
      });

      macdChartRef.current = chart;
      macdHistRef.current = histSeries;
      macdLineRef.current = lineSeries;
      macdSignalRef.current = signalSeries;

      syncTimeScales(mainChartRef.current, chart);

      const handleResize = () => {
        if (macdContainerRef.current) {
          chart.applyOptions({ width: macdContainerRef.current.clientWidth });
        }
      };
      window.addEventListener("resize", handleResize);
      return () => {
        window.removeEventListener("resize", handleResize);
      };
    }
  }, [showMacd]);

  // Update MACD data
  useEffect(() => {
    if (!indicatorData) return;

    const visible = indicatorData.slice(0, visibleCount);

    if (macdLineRef.current) {
      macdLineRef.current.setData(
        visible
          .filter((d) => d.macd !== null && d.macd !== undefined)
          .map((d) => ({ time: d.time as Time, value: d.macd as number }))
      );
    }
    if (macdSignalRef.current) {
      macdSignalRef.current.setData(
        visible
          .filter((d) => d.macd_signal !== null && d.macd_signal !== undefined)
          .map((d) => ({ time: d.time as Time, value: d.macd_signal as number }))
      );
    }
    if (macdHistRef.current) {
      macdHistRef.current.setData(
        visible
          .filter((d) => d.macd_histogram !== null && d.macd_histogram !== undefined)
          .map((d) => ({
            time: d.time as Time,
            value: d.macd_histogram as number,
            color: (d.macd_histogram as number) >= 0
              ? indicatorColors.macd_histogram_pos
              : indicatorColors.macd_histogram_neg,
          }))
      );
    }
  }, [indicatorData, visibleCount, showMacd]);

  // ── Time scale sync helper ────────────────────────────────────────
  const syncTimeScales = useCallback(
    (source: IChartApi | null, target: IChartApi | null) => {
      if (!source || !target) return;

      source.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (syncingRef.current || !range) return;
        syncingRef.current = true;
        target.timeScale().setVisibleLogicalRange(range);
        syncingRef.current = false;
      });

      target.timeScale().subscribeVisibleLogicalRangeChange((range) => {
        if (syncingRef.current || !range) return;
        syncingRef.current = true;
        source.timeScale().setVisibleLogicalRange(range);
        syncingRef.current = false;
      });
    },
    []
  );

  return (
    <div className="w-full space-y-0">
      {/* Main chart */}
      <div className="relative">
        <div
          ref={mainContainerRef}
          className="rounded-t-lg border border-neutral-700"
        />
        {/* Tooltip */}
        {tooltipData && (
          <div className="absolute top-3 left-3 z-10 rounded-lg border border-neutral-700 bg-neutral-900/95 px-3 py-2 shadow-xl backdrop-blur-sm">
            <p className="text-xs text-neutral-400 mb-1">{tooltipData.time}</p>
            <div className="grid grid-cols-2 gap-x-3 text-xs">
              <span className="text-neutral-400">O: <span className="font-mono text-neutral-100">{tooltipData.open.toLocaleString()}</span></span>
              <span className="text-neutral-400">H: <span className="font-mono text-neutral-100">{tooltipData.high.toLocaleString()}</span></span>
              <span className="text-neutral-400">L: <span className="font-mono text-neutral-100">{tooltipData.low.toLocaleString()}</span></span>
              <span className="text-neutral-400">C: <span className="font-mono text-neutral-100">{tooltipData.close.toLocaleString()}</span></span>
            </div>
          </div>
        )}
      </div>

      {/* RSI sub-chart */}
      {showRsi && (
        <div
          ref={rsiContainerRef}
          className="border-x border-neutral-700 relative"
        >
          <span className="absolute top-1 left-2 z-10 text-[10px] text-neutral-500 font-mono">RSI (14)</span>
        </div>
      )}

      {/* MACD sub-chart */}
      {showMacd && (
        <div
          ref={macdContainerRef}
          className="border-x border-neutral-700 relative"
        >
          <span className="absolute top-1 left-2 z-10 text-[10px] text-neutral-500 font-mono">MACD (12,26,9)</span>
        </div>
      )}

      {/* Bottom border */}
      <div className={`h-0 border-b border-neutral-700 ${showRsi || showMacd ? "" : "rounded-b-lg"}`} />
    </div>
  );
}
