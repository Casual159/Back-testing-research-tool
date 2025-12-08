"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType } from "lightweight-charts";

interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface RegimeData {
  time: number;
  regime: string;
  full_regime: string;
  trend_state: string;
  volatility_state: string;
  momentum_state: string;
  confidence: number;
  color: string;
}

interface CandlestickChartProps {
  data: CandleData[];
  symbol: string;
  timeframe: string;
  regimeData?: RegimeData[];
  showRegime?: boolean;
}

export default function CandlestickChart({
  data,
  symbol,
  timeframe,
  regimeData,
  showRegime = true
}: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#1a1a1a" },
        textColor: "#d1d5db",
      },
      grid: {
        vertLines: { color: "#2a2a2a" },
        horzLines: { color: "#2a2a2a" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 600,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: "#2a2a2a",
      },
      leftPriceScale: {
        visible: true,
        borderColor: "#2a2a2a",
      },
    });

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    // Add volume series on left scale
    const volumeSeries = chart.addHistogramSeries({
      color: "#3b82f6",
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "left",
    });

    // Set volume scale height to 20% of chart
    chart.priceScale("left").applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // Add regime series if data is provided and should be shown
    let regimeSeries;
    if (regimeData && showRegime && regimeData.length > 0) {
      regimeSeries = chart.addHistogramSeries({
        priceFormat: {
          type: "custom",
          formatter: () => "", // No price labels
        },
        priceScaleId: "regime",
      });

      // Position regime bar at the very bottom (below volume)
      chart.priceScale("regime").applyOptions({
        scaleMargins: {
          top: 0.95, // 95% offset - shows as bottom bar
          bottom: 0,
        },
      });

      // Prepare regime data - map each regime to a colored histogram bar
      const regimeHistogramData = regimeData.map((r) => ({
        time: r.time as any, // Cast to Time type for lightweight-charts
        value: 1, // Fixed height for all regime bars
        color: r.color,
      }));

      regimeSeries.setData(regimeHistogramData);
    }

    // Prepare candle data
    const candleData = data.map((candle) => ({
      time: candle.time as any, // Cast to Time type for lightweight-charts
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    // Prepare volume data with coloring based on candle direction
    const volumeData = data.map((candle) => ({
      time: candle.time as any, // Cast to Time type for lightweight-charts
      value: candle.volume,
      color: candle.close >= candle.open ? "#22c55e80" : "#ef444480", // Semi-transparent
    }));

    // Set data
    candleSeries.setData(candleData);
    volumeSeries.setData(volumeData);

    // Fit content to visible range
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data, regimeData, showRegime]);

  return (
    <div className="w-full">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">
            {symbol} - {timeframe}
          </h2>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            {data.length.toLocaleString()} candles
          </p>
        </div>
      </div>
      <div
        ref={chartContainerRef}
        className="rounded-lg border border-neutral-300 dark:border-neutral-700"
      />
    </div>
  );
}
