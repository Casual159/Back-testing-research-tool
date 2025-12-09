"use client";

import { useEffect, useRef, useState } from "react";
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

interface TooltipData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  regime?: {
    simplified: string;
    full_regime: string;
    trend_state: string;
    volatility_state: string;
    momentum_state: string;
    confidence: number;
    color: string;
  };
}

export default function CandlestickChart({
  data,
  symbol,
  timeframe,
  regimeData,
  showRegime = true
}: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [tooltipData, setTooltipData] = useState<TooltipData | null>(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);

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

    // Subscribe to crosshair move for tooltip
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.point) {
        setTooltipVisible(false);
        return;
      }

      // Find candle data for this time
      const candle = data.find((c) => c.time === param.time);
      if (!candle) {
        setTooltipVisible(false);
        return;
      }

      // Find regime data for this time (if available)
      const regime = regimeData?.find((r) => r.time === param.time);

      // Format time
      const date = new Date((param.time as number) * 1000);
      const timeStr = date.toLocaleString();

      setTooltipData({
        time: timeStr,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume,
        regime: regime ? {
          simplified: regime.regime,
          full_regime: regime.full_regime,
          trend_state: regime.trend_state,
          volatility_state: regime.volatility_state,
          momentum_state: regime.momentum_state,
          confidence: regime.confidence,
          color: regime.color,
        } : undefined,
      });
      setTooltipVisible(true);
    });

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
      <div className="relative">
        <div
          ref={chartContainerRef}
          className="rounded-lg border border-neutral-300 dark:border-neutral-700"
        />

        {/* Tooltip */}
        {tooltipVisible && tooltipData && (
          <div className="absolute top-4 left-4 z-10 rounded-lg border border-neutral-700 bg-neutral-900/95 p-4 shadow-xl backdrop-blur-sm">
            <div className="space-y-3">
              {/* Time */}
              <div className="border-b border-neutral-700 pb-2">
                <p className="text-xs text-neutral-400">{tooltipData.time}</p>
              </div>

              {/* OHLCV */}
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                <div>
                  <span className="text-neutral-400">O:</span>{" "}
                  <span className="font-mono text-neutral-100">
                    ${tooltipData.open.toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-neutral-400">H:</span>{" "}
                  <span className="font-mono text-neutral-100">
                    ${tooltipData.high.toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-neutral-400">L:</span>{" "}
                  <span className="font-mono text-neutral-100">
                    ${tooltipData.low.toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-neutral-400">C:</span>{" "}
                  <span className="font-mono text-neutral-100">
                    ${tooltipData.close.toLocaleString()}
                  </span>
                </div>
                <div className="col-span-2">
                  <span className="text-neutral-400">Vol:</span>{" "}
                  <span className="font-mono text-neutral-100">
                    {tooltipData.volume.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Regime Info */}
              {tooltipData.regime && showRegime && (
                <>
                  <div className="border-t border-neutral-700 pt-2">
                    <p className="text-xs font-semibold text-neutral-300 mb-2">
                      Market Regime
                    </p>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-3 w-3 rounded"
                        style={{ backgroundColor: tooltipData.regime.color }}
                      />
                      <span className="font-semibold text-neutral-100">
                        {tooltipData.regime.simplified}
                      </span>
                    </div>
                    <div className="space-y-1 text-xs">
                      <div>
                        <span className="text-neutral-400">Trend:</span>{" "}
                        <span className="text-neutral-200">
                          {tooltipData.regime.trend_state}
                        </span>
                      </div>
                      <div>
                        <span className="text-neutral-400">Volatility:</span>{" "}
                        <span className="text-neutral-200">
                          {tooltipData.regime.volatility_state}
                        </span>
                      </div>
                      <div>
                        <span className="text-neutral-400">Momentum:</span>{" "}
                        <span className="text-neutral-200">
                          {tooltipData.regime.momentum_state}
                        </span>
                      </div>
                      <div>
                        <span className="text-neutral-400">Confidence:</span>{" "}
                        <span className="font-mono text-neutral-200">
                          {(tooltipData.regime.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="pt-1 text-neutral-500">
                        {tooltipData.regime.full_regime}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
