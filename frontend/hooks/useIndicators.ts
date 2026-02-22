"use client";

import { useState, useRef, useCallback } from "react";
import { apiEndpoint } from "@/lib/config";
import type { IndicatorData, IndicatorId } from "@/components/backtest/BacktestChart";

// Which backend indicator keys to request for each frontend indicator ID
const INDICATOR_BACKEND_MAP: Record<string, string> = {
  sma_20: "sma_20",
  sma_50: "sma_50",
  sma_200: "sma_200",
  ema_12: "ema_12",
  ema_26: "ema_26",
  rsi: "rsi",
  macd: "macd",
  macd_signal: "macd",
  macd_histogram: "macd",
  bb_upper: "bollinger",
  bb_middle: "bollinger",
  bb_lower: "bollinger",
};

export function useIndicators(
  symbol: string,
  timeframe: string,
  startDate: string,
  endDate: string
) {
  const [data, setData] = useState<IndicatorData[] | null>(null);
  const [loading, setLoading] = useState(false);
  const cacheRef = useRef<Map<string, IndicatorData[]>>(new Map());

  const fetchIndicators = useCallback(
    async (enabledIds: IndicatorId[]) => {
      if (enabledIds.length === 0) {
        setData(null);
        return;
      }

      // Map frontend IDs to unique backend indicator keys
      const backendKeys = [...new Set(enabledIds.map((id) => INDICATOR_BACKEND_MAP[id]))];
      const cacheKey = `${symbol}|${timeframe}|${startDate}|${endDate}|${backendKeys.sort().join(",")}`;

      if (cacheRef.current.has(cacheKey)) {
        setData(cacheRef.current.get(cacheKey)!);
        return;
      }

      setLoading(true);
      try {
        const params = new URLSearchParams({
          indicators: backendKeys.join(","),
        });
        if (startDate) params.set("start_date", startDate);
        if (endDate) params.set("end_date", endDate);

        const res = await fetch(
          apiEndpoint(`/data/indicators/${symbol}/${timeframe}?${params}`)
        );
        if (!res.ok) throw new Error("Failed to fetch indicators");

        const json: IndicatorData[] = await res.json();
        cacheRef.current.set(cacheKey, json);
        setData(json);
      } catch (err) {
        console.error("Failed to fetch indicators:", err);
      } finally {
        setLoading(false);
      }
    },
    [symbol, timeframe, startDate, endDate]
  );

  return { data, loading, fetchIndicators };
}
