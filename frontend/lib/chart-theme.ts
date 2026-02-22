import { ColorType } from "lightweight-charts";

export const chartColors = {
  background: "#1a1a1a",
  text: "#d1d5db",
  grid: "#2a2a2a",
  upCandle: "#22c55e",
  downCandle: "#ef4444",
  volumeUp: "#22c55e80",
  volumeDown: "#ef444480",
  volumeBase: "#3b82f6",
  crosshair: "#666",
} as const;

export const regimeColors: Record<string, string> = {
  TREND_UP: "#22c55e",
  TREND_DOWN: "#ef4444",
  RANGE: "#3b82f6",
  CHOPPY: "#f59e0b",
  NEUTRAL: "#6b7280",
};

export const indicatorColors = {
  sma_20: "#f59e0b",
  sma_50: "#3b82f6",
  sma_200: "#ef4444",
  ema_12: "#06b6d4",
  ema_26: "#8b5cf6",
  bb_upper: "#6b728080",
  bb_middle: "#6b7280",
  bb_lower: "#6b728080",
  rsi: "#a855f7",
  macd: "#3b82f6",
  macd_signal: "#f59e0b",
  macd_histogram_pos: "#22c55e80",
  macd_histogram_neg: "#ef444480",
} as const;

export const defaultChartOptions = {
  layout: {
    background: { type: ColorType.Solid as const, color: chartColors.background },
    textColor: chartColors.text,
  },
  grid: {
    vertLines: { color: chartColors.grid },
    horzLines: { color: chartColors.grid },
  },
  timeScale: {
    timeVisible: true,
    secondsVisible: false,
  },
  rightPriceScale: {
    borderColor: chartColors.grid,
  },
  crosshairMarkerVisible: true,
};
