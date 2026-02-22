"use client";

import { indicatorColors } from "@/lib/chart-theme";
import type { IndicatorId } from "./BacktestChart";

interface IndicatorConfig {
  id: IndicatorId;
  label: string;
  group: "overlay" | "oscillator";
  color: string;
}

const INDICATORS: IndicatorConfig[] = [
  { id: "sma_20", label: "SMA 20", group: "overlay", color: indicatorColors.sma_20 },
  { id: "sma_50", label: "SMA 50", group: "overlay", color: indicatorColors.sma_50 },
  { id: "sma_200", label: "SMA 200", group: "overlay", color: indicatorColors.sma_200 },
  { id: "ema_12", label: "EMA 12", group: "overlay", color: indicatorColors.ema_12 },
  { id: "ema_26", label: "EMA 26", group: "overlay", color: indicatorColors.ema_26 },
  { id: "bb_upper", label: "BB Upper", group: "overlay", color: indicatorColors.bb_upper },
  { id: "bb_middle", label: "BB Middle", group: "overlay", color: indicatorColors.bb_middle },
  { id: "bb_lower", label: "BB Lower", group: "overlay", color: indicatorColors.bb_lower },
  { id: "rsi", label: "RSI (14)", group: "oscillator", color: indicatorColors.rsi },
  { id: "macd", label: "MACD", group: "oscillator", color: indicatorColors.macd },
  { id: "macd_signal", label: "Signal", group: "oscillator", color: indicatorColors.macd_signal },
  { id: "macd_histogram", label: "Histogram", group: "oscillator", color: indicatorColors.macd_histogram_pos },
];

interface IndicatorPanelProps {
  enabled: IndicatorId[];
  onChange: (enabled: IndicatorId[]) => void;
  loading?: boolean;
}

export default function IndicatorPanel({ enabled, onChange, loading }: IndicatorPanelProps) {
  const toggle = (id: IndicatorId) => {
    if (enabled.includes(id)) {
      onChange(enabled.filter((e) => e !== id));
    } else {
      onChange([...enabled, id]);
    }
  };

  // Quick toggles for Bollinger Bands and MACD groups
  const toggleGroup = (ids: IndicatorId[]) => {
    const allEnabled = ids.every((id) => enabled.includes(id));
    if (allEnabled) {
      onChange(enabled.filter((e) => !ids.includes(e)));
    } else {
      onChange([...new Set([...enabled, ...ids])]);
    }
  };

  const overlays = INDICATORS.filter((i) => i.group === "overlay");
  const oscillators = INDICATORS.filter((i) => i.group === "oscillator");

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
      <span className="text-neutral-500 font-medium">Indicators</span>

      {/* Overlay indicators */}
      <div className="flex flex-wrap items-center gap-1.5">
        {overlays.map((ind) => {
          // Group BB as a single toggle
          if (ind.id === "bb_upper" || ind.id === "bb_lower") return null;
          if (ind.id === "bb_middle") {
            const bbIds: IndicatorId[] = ["bb_upper", "bb_middle", "bb_lower"];
            const allBb = bbIds.every((id) => enabled.includes(id));
            return (
              <button
                key="bollinger"
                onClick={() => toggleGroup(bbIds)}
                className={`rounded px-2 py-0.5 border transition-colors ${
                  allBb
                    ? "border-neutral-500 bg-neutral-700 text-neutral-200"
                    : "border-neutral-700 text-neutral-500 hover:text-neutral-300"
                }`}
              >
                <span className="inline-block w-2 h-2 rounded-full mr-1" style={{ backgroundColor: ind.color }} />
                Bollinger
              </button>
            );
          }
          return (
            <button
              key={ind.id}
              onClick={() => toggle(ind.id)}
              className={`rounded px-2 py-0.5 border transition-colors ${
                enabled.includes(ind.id)
                  ? "border-neutral-500 bg-neutral-700 text-neutral-200"
                  : "border-neutral-700 text-neutral-500 hover:text-neutral-300"
              }`}
            >
              <span className="inline-block w-2 h-2 rounded-full mr-1" style={{ backgroundColor: ind.color }} />
              {ind.label}
            </button>
          );
        })}
      </div>

      <span className="text-neutral-700">|</span>

      {/* Oscillators */}
      <div className="flex flex-wrap items-center gap-1.5">
        {/* RSI standalone */}
        <button
          onClick={() => toggle("rsi")}
          className={`rounded px-2 py-0.5 border transition-colors ${
            enabled.includes("rsi")
              ? "border-neutral-500 bg-neutral-700 text-neutral-200"
              : "border-neutral-700 text-neutral-500 hover:text-neutral-300"
          }`}
        >
          <span className="inline-block w-2 h-2 rounded-full mr-1" style={{ backgroundColor: indicatorColors.rsi }} />
          RSI
        </button>

        {/* MACD group toggle */}
        <button
          onClick={() => toggleGroup(["macd", "macd_signal", "macd_histogram"])}
          className={`rounded px-2 py-0.5 border transition-colors ${
            ["macd", "macd_signal", "macd_histogram"].every((id) => enabled.includes(id as IndicatorId))
              ? "border-neutral-500 bg-neutral-700 text-neutral-200"
              : "border-neutral-700 text-neutral-500 hover:text-neutral-300"
          }`}
        >
          <span className="inline-block w-2 h-2 rounded-full mr-1" style={{ backgroundColor: indicatorColors.macd }} />
          MACD
        </button>
      </div>

      {loading && (
        <div className="h-3 w-3 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      )}
    </div>
  );
}
