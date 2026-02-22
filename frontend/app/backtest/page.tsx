"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ArrowLeft, PlayCircle, TrendingUp, TrendingDown,
  BarChart3, Activity, Target, AlertCircle, CheckCircle
} from "lucide-react";
import Link from "next/link";
import { apiEndpoint } from "@/lib/config";
import BacktestChart, { CandleData, IndicatorId } from "@/components/backtest/BacktestChart";
import IndicatorPanel from "@/components/backtest/IndicatorPanel";
import { useIndicators } from "@/hooks/useIndicators";
import { usePlaybackEngine } from "@/hooks/usePlaybackEngine";
import PlaybackControls from "@/components/backtest/PlaybackControls";
import PlaybackEquityCurve from "@/components/backtest/PlaybackEquityCurve";

interface Strategy {
  name: string;
  description: string;
  strategy_type: string;
}

interface Dataset {
  symbol: string;
  timeframe: string;
  candle_count: number;
  first_candle: string;
  last_candle: string;
}

interface Trade {
  entry_time: string;
  entry_price: number;
  exit_time: string;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
  duration_hours: number;
}

interface BacktestResult {
  success: boolean;
  strategy_name: string;
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  // Flat metrics from API
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  total_trades: number;
  profit_factor: number;
  // Data
  trades: Trade[];
  equity_curve: { time: string; value: number }[];
  regime_stats?: Record<string, unknown>;
}

// Metric interpretation helpers
function interpretSharpe(value: number): { label: string; color: string } {
  if (value < 0) return { label: "Losing", color: "text-red-600" };
  if (value < 1) return { label: "Poor", color: "text-orange-600" };
  if (value < 2) return { label: "Good", color: "text-green-600" };
  return { label: "Excellent", color: "text-emerald-600" };
}

function interpretWinRate(value: number): { label: string; color: string } {
  if (value < 40) return { label: "Low", color: "text-red-600" };
  if (value < 50) return { label: "Average", color: "text-orange-600" };
  if (value < 60) return { label: "Good", color: "text-green-600" };
  return { label: "High", color: "text-emerald-600" };
}

function interpretDrawdown(value: number): { label: string; color: string } {
  const absValue = Math.abs(value);
  if (absValue < 10) return { label: "Excellent", color: "text-emerald-600" };
  if (absValue < 20) return { label: "Acceptable", color: "text-green-600" };
  if (absValue < 30) return { label: "High", color: "text-orange-600" };
  return { label: "Very High", color: "text-red-600" };
}

function BacktestPageContent() {
  const searchParams = useSearchParams();
  const initialStrategy = searchParams.get("strategy") || "";

  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState(initialStrategy);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string>("");
  const [showFetchDialog, setShowFetchDialog] = useState(false);
  const [datasetSelected, setDatasetSelected] = useState(false); // Flag to skip availability check
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1h");
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-03-31");
  const [initialCapital, setInitialCapital] = useState(10000);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dataAvailable, setDataAvailable] = useState<boolean | null>(null);
  const [checkingData, setCheckingData] = useState(false);
  const [candleData, setCandleData] = useState<CandleData[]>([]);
  const [enabledIndicators, setEnabledIndicators] = useState<IndicatorId[]>([]);
  const indicators = useIndicators(symbol, timeframe, startDate, endDate);
  const playback = usePlaybackEngine(candleData.length);

  // Load strategies on mount
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const response = await fetch(apiEndpoint("/strategies"));
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // Ensure data is an array
        if (Array.isArray(data)) {
          setStrategies(data);

          // If initial strategy is provided and valid, select it
          if (initialStrategy && data.some((s: Strategy) => s.name === initialStrategy)) {
            setSelectedStrategy(initialStrategy);
          }
        } else {
          console.error("Strategies response is not an array:", data);
          setStrategies([]);
        }
      } catch (err) {
        console.error("Failed to load strategies:", err);
        setStrategies([]);  // Ensure strategies remains an array
      }
    };
    loadStrategies();
  }, [initialStrategy]);

  // Load datasets on mount
  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const response = await fetch(apiEndpoint("/data/stats"));
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (Array.isArray(data)) {
          setDatasets(data);
        } else {
          console.error("Datasets response is not an array:", data);
          setDatasets([]);
        }
      } catch (err) {
        console.error("Failed to load datasets:", err);
        setDatasets([]);
      }
    };
    loadDatasets();
  }, []);

  // Handler for dataset selection
  const handleDatasetChange = (datasetKey: string) => {
    setSelectedDataset(datasetKey);

    if (datasetKey === "fetch-new") {
      setShowFetchDialog(true);
      return;
    }

    if (!datasetKey) {
      setDatasetSelected(false);
      return;
    }

    // Parse dataset key: "BTCUSDT|1h"
    const [sym, tf] = datasetKey.split("|");
    const dataset = datasets.find(d => d.symbol === sym && d.timeframe === tf);

    if (dataset) {
      // Set flag to skip automatic availability check
      setDatasetSelected(true);
      setUserInteracted(true);

      setSymbol(dataset.symbol);
      setTimeframe(dataset.timeframe);

      // Parse dates from ISO strings - handle timezone by parsing date parts directly
      const firstDate = dataset.first_candle.split('T')[0];
      const lastDate = dataset.last_candle.split('T')[0];

      setStartDate(firstDate);
      setEndDate(lastDate);
      setDataAvailable(true);
    }
  };

  // Track whether user has interacted with dataset/params
  const [userInteracted, setUserInteracted] = useState(false);

  // Check data availability when params change (only after user interaction)
  useEffect(() => {
    const checkData = async () => {
      if (!symbol || !timeframe || !userInteracted) return;

      // Skip check if dataset was just selected from dropdown (we know it exists)
      if (datasetSelected) {
        setDatasetSelected(false); // Reset flag
        return;
      }

      setCheckingData(true);
      try {
        const params = new URLSearchParams({
          start_date: startDate,
          end_date: endDate,
        });
        const response = await fetch(
          apiEndpoint(`/data/check/${symbol}/${timeframe}?${params}`)
        );
        const data = await response.json();
        setDataAvailable(data.available);
      } catch (err) {
        setDataAvailable(null);
      } finally {
        setCheckingData(false);
      }
    };

    const debounce = setTimeout(checkData, 500);
    return () => clearTimeout(debounce);
  }, [symbol, timeframe, startDate, endDate, datasetSelected, userInteracted]);

  const handleIndicatorsChange = (newEnabled: IndicatorId[]) => {
    setEnabledIndicators(newEnabled);
    if (newEnabled.length > 0) {
      indicators.fetchIndicators(newEnabled);
    }
  };

  const handleRunBacktest = async () => {
    if (!selectedStrategy) {
      setError("Please select a strategy");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(apiEndpoint("/backtest"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy_name: selectedStrategy,
          symbol,
          timeframe,
          start_date: startDate,
          end_date: endDate,
          initial_capital: initialCapital,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Backtest failed");
      }

      setResult(data);

      // Fetch candle data for chart visualization
      try {
        const params = new URLSearchParams();
        if (startDate) params.set("start_date", startDate);
        if (endDate) params.set("end_date", endDate);
        const candleRes = await fetch(
          apiEndpoint(`/data/candles/${symbol}/${timeframe}?${params}`)
        );
        if (candleRes.ok) {
          const candles = await candleRes.json();
          setCandleData(candles);
        }
      } catch {
        // Chart is optional - don't fail the whole page
      }
    } catch (err) {
      setError(`Backtest failed: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center gap-4">
          <Link href="/">
            <Button variant="outline" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Run Backtest</h1>
            <p className="text-neutral-600 dark:text-neutral-400">
              Test trading strategies on historical data
            </p>
          </div>
        </div>

        {/* Configuration Bar — inline at top */}
        <Card className="mb-6">
          <CardContent className="py-4">
            <div className="flex flex-wrap items-end gap-4">
              {/* Strategy */}
              <div className="space-y-1 min-w-[200px] flex-1">
                <label className="text-xs font-medium text-neutral-400">Strategy</label>
                <select
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value)}
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-800 dark:text-white"
                >
                  <option value="">Select a strategy...</option>
                  {strategies.map((s) => (
                    <option key={s.name} value={s.name}>
                      {s.name} ({s.strategy_type})
                    </option>
                  ))}
                </select>
              </div>

              {/* Dataset */}
              <div className="space-y-1 min-w-[260px] flex-[2]">
                <label className="text-xs font-medium text-neutral-400">Dataset</label>
                <select
                  value={selectedDataset}
                  onChange={(e) => handleDatasetChange(e.target.value)}
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-800 dark:text-white"
                >
                  <option value="">Select a dataset...</option>
                  {datasets.map((ds) => {
                    const key = `${ds.symbol}|${ds.timeframe}`;
                    const firstDate = new Date(ds.first_candle).toISOString().split('T')[0];
                    const lastDate = new Date(ds.last_candle).toISOString().split('T')[0];
                    const label = `${ds.symbol} ${ds.timeframe} (${ds.candle_count} bars) ${firstDate} → ${lastDate}`;
                    return (
                      <option key={key} value={key}>
                        {label}
                      </option>
                    );
                  })}
                  <option value="fetch-new" className="font-semibold text-blue-600">
                    + Fetch new data...
                  </option>
                </select>
              </div>

              {/* Initial Capital */}
              <div className="space-y-1 w-[130px]">
                <label className="text-xs font-medium text-neutral-400">Capital ($)</label>
                <input
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(Number(e.target.value))}
                  className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-600 dark:bg-neutral-800 dark:text-white"
                  min={100}
                  step={1000}
                />
              </div>

              {/* Data status indicator */}
              {userInteracted && (
                <div className="flex items-center gap-1.5 pb-1">
                  {checkingData ? (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                  ) : dataAvailable === true ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : dataAvailable === false ? (
                    <AlertCircle className="h-4 w-4 text-red-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-neutral-400" />
                  )}
                  <span className="text-xs whitespace-nowrap">
                    {checkingData
                      ? "Checking..."
                      : dataAvailable === true
                      ? "Data OK"
                      : dataAvailable === false
                      ? "No data"
                      : ""}
                  </span>
                </div>
              )}

              {/* Run Button */}
              <Button
                onClick={handleRunBacktest}
                disabled={loading || !selectedStrategy || dataAvailable === false}
                className="h-[38px]"
              >
                {loading ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Running...
                  </>
                ) : (
                  <>
                    <PlayCircle className="mr-2 h-4 w-4" />
                    Run Backtest
                  </>
                )}
              </Button>
            </div>

            {/* Second row: dataset info + errors */}
            {(selectedDataset && selectedDataset !== "fetch-new") && (
              <p className="text-xs text-neutral-500 mt-2">
                {symbol} {timeframe}: {startDate} → {endDate}
              </p>
            )}
            {dataAvailable === false && (
              <Link href="/data" className="text-xs text-blue-600 hover:underline mt-1 inline-block">
                Go to Data Management to fetch data
              </Link>
            )}
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300 mt-3">
                {error}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results — full width */}
        {result ? (
          <div className="space-y-6">
            {/* Candlestick Chart with Trade Markers */}
            {candleData.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <CardTitle className="text-lg">
                        {result.symbol} {result.timeframe} — {result.strategy_name}
                      </CardTitle>
                      <CardDescription>
                        {candleData.length.toLocaleString()} candles · {result.trades.length} trades
                      </CardDescription>
                    </div>
                  </div>
                  <IndicatorPanel
                    enabled={enabledIndicators}
                    onChange={handleIndicatorsChange}
                    loading={indicators.loading}
                  />
                </CardHeader>
                <CardContent className="px-2 pb-2 space-y-3">
                  <BacktestChart
                    candles={candleData}
                    trades={result.trades}
                    playbackIndex={playback.playbackIndex}
                    indicatorData={indicators.data ?? undefined}
                    enabledIndicators={enabledIndicators}
                  />
                  <PlaybackControls
                    state={playback.state}
                    onPlay={playback.play}
                    onPause={playback.pause}
                    onStop={playback.stop}
                    onSeek={playback.seek}
                    onSetSpeed={playback.setSpeed}
                    candleTimes={candleData.map((c) => c.time)}
                  />
                </CardContent>
              </Card>
            )}

            {/* Metrics Cards */}
            <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
              <MetricCard
                title="Total Return"
                value={`${result.total_return_pct >= 0 ? "+" : ""}${result.total_return_pct.toFixed(2)}%`}
                icon={result.total_return_pct >= 0 ? TrendingUp : TrendingDown}
                iconColor={result.total_return_pct >= 0 ? "text-green-600" : "text-red-600"}
                valueColor={result.total_return_pct >= 0 ? "text-green-600" : "text-red-600"}
              />
              <MetricCard
                title="Sharpe Ratio"
                value={result.sharpe_ratio.toFixed(2)}
                subtitle={interpretSharpe(result.sharpe_ratio).label}
                icon={BarChart3}
                iconColor="text-blue-600"
                valueColor={interpretSharpe(result.sharpe_ratio).color}
              />
              <MetricCard
                title="Max Drawdown"
                value={`${result.max_drawdown_pct.toFixed(2)}%`}
                subtitle={interpretDrawdown(result.max_drawdown_pct).label}
                icon={TrendingDown}
                iconColor="text-orange-600"
                valueColor={interpretDrawdown(result.max_drawdown_pct).color}
              />
              <MetricCard
                title="Win Rate"
                value={`${result.win_rate_pct.toFixed(1)}%`}
                subtitle={interpretWinRate(result.win_rate_pct).label}
                icon={Target}
                iconColor="text-purple-600"
                valueColor={interpretWinRate(result.win_rate_pct).color}
              />
              <MetricCard
                title="Total Trades"
                value={String(result.total_trades)}
                subtitle={result.total_trades < 10 ? "Low sample size" : "Statistically valid"}
                icon={Activity}
                iconColor="text-cyan-600"
              />
              <MetricCard
                title="Profit Factor"
                value={result.profit_factor.toFixed(2)}
                subtitle={result.profit_factor > 1.5 ? "Good edge" : result.profit_factor > 1 ? "Marginal" : "Losing"}
                icon={BarChart3}
                iconColor="text-emerald-600"
                valueColor={result.profit_factor > 1.5 ? "text-emerald-600" : result.profit_factor > 1 ? "text-orange-600" : "text-red-600"}
              />
            </div>

            {/* Equity Curve */}
            <Card>
              <CardHeader>
                <CardTitle>Equity Curve</CardTitle>
                <CardDescription>
                  Portfolio value over time (${initialCapital.toLocaleString()} initial)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <PlaybackEquityCurve
                  data={result.equity_curve}
                  initialCapital={initialCapital}
                  playbackIndex={playback.playbackIndex}
                />
              </CardContent>
            </Card>

            {/* Trade List */}
            <Card>
              <CardHeader>
                <CardTitle>Trade History</CardTitle>
                <CardDescription>
                  {result.trades.length} trades executed
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="max-h-80 overflow-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-card">
                      <tr className="border-b">
                        <th className="py-2 text-left font-medium">Entry</th>
                        <th className="py-2 text-left font-medium">Exit</th>
                        <th className="py-2 text-right font-medium">Entry Price</th>
                        <th className="py-2 text-right font-medium">Exit Price</th>
                        <th className="py-2 text-right font-medium">P&L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trades.map((trade, idx) => (
                        <tr key={idx} className="border-b last:border-0">
                          <td className="py-2 text-neutral-600 dark:text-neutral-400">
                            {new Date(trade.entry_time).toLocaleDateString()}
                          </td>
                          <td className="py-2 text-neutral-600 dark:text-neutral-400">
                            {new Date(trade.exit_time).toLocaleDateString()}
                          </td>
                          <td className="py-2 text-right">${trade.entry_price.toLocaleString()}</td>
                          <td className="py-2 text-right">${trade.exit_price.toLocaleString()}</td>
                          <td className={`py-2 text-right font-medium ${trade.pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                            {trade.pnl >= 0 ? "+" : ""}{trade.pnl_pct.toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <Card className="flex items-center justify-center py-20">
            <CardContent className="text-center">
              <BarChart3 className="mx-auto h-16 w-16 text-neutral-300 mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Results Yet</h3>
              <p className="text-neutral-600 dark:text-neutral-400">
                Configure parameters and run a backtest to see results
              </p>
            </CardContent>
          </Card>
        )}

        {/* Fetch Data Dialog */}
        {showFetchDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle>Fetch New Data</CardTitle>
                <CardDescription>
                  Navigate to Data Management to fetch historical data
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  The Data Management page allows you to fetch historical price data
                  from Binance for any symbol and timeframe.
                </p>
                <div className="flex gap-2">
                  <Link href="/data" className="flex-1">
                    <Button className="w-full">
                      Go to Data Management
                    </Button>
                  </Link>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowFetchDialog(false);
                      setSelectedDataset("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor,
  valueColor,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ElementType;
  iconColor: string;
  valueColor?: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400">{title}</p>
            <p className={`text-2xl font-bold mt-1 ${valueColor || ""}`}>{value}</p>
            {subtitle && (
              <p className="text-xs text-neutral-500 mt-1">{subtitle}</p>
            )}
          </div>
          <Icon className={`h-5 w-5 ${iconColor}`} />
        </div>
      </CardContent>
    </Card>
  );
}

export default function BacktestPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    }>
      <BacktestPageContent />
    </Suspense>
  );
}
