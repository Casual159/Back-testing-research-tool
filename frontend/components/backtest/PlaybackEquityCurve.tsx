"use client";

import { useEffect, useRef } from "react";
import { createChart, IChartApi, ISeriesApi, Time } from "lightweight-charts";
import { chartColors, defaultChartOptions } from "@/lib/chart-theme";

interface EquityPoint {
  time: string;
  value: number;
}

interface PlaybackEquityCurveProps {
  data: EquityPoint[];
  initialCapital: number;
  playbackIndex?: number | null; // null = show all
}

function isoToUnix(iso: string): number {
  return Math.floor(new Date(iso).getTime() / 1000);
}

export default function PlaybackEquityCurve({
  data,
  initialCapital,
  playbackIndex = null,
}: PlaybackEquityCurveProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const areaSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);

  const visibleCount = playbackIndex !== null ? playbackIndex + 1 : data.length;

  // Create chart
  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      ...defaultChartOptions,
      width: containerRef.current.clientWidth,
      height: 150,
      rightPriceScale: {
        borderColor: chartColors.grid,
      },
    });

    const finalValue = data[data.length - 1]?.value ?? initialCapital;
    const isProfit = finalValue >= initialCapital;

    const areaSeries = chart.addAreaSeries({
      lineColor: isProfit ? "#22c55e" : "#ef4444",
      topColor: isProfit ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)",
      bottomColor: isProfit ? "rgba(34, 197, 94, 0.02)" : "rgba(239, 68, 68, 0.02)",
      lineWidth: 2,
      priceFormat: { type: "custom", formatter: (v: number) => `$${v.toLocaleString()}` },
    });

    // Initial capital reference line
    areaSeries.createPriceLine({
      price: initialCapital,
      color: "#94a3b860",
      lineWidth: 1,
      lineStyle: 2,
      axisLabelVisible: true,
    });

    chartRef.current = chart;
    areaSeriesRef.current = areaSeries;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
      areaSeriesRef.current = null;
    };
  }, [data.length > 0 ? data[0].time : "", initialCapital]);

  // Update data based on playback
  useEffect(() => {
    if (!areaSeriesRef.current) return;

    const visible = data.slice(0, visibleCount).map((d) => ({
      time: isoToUnix(d.time) as Time,
      value: d.value,
    }));

    areaSeriesRef.current.setData(visible);

    if (playbackIndex === null && chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [visibleCount, data]);

  if (data.length === 0) {
    return (
      <div className="h-[150px] flex items-center justify-center text-neutral-400 text-sm">
        No equity curve data
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="rounded-lg border border-neutral-700"
    />
  );
}
