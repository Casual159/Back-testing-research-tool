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

interface Strategy {
  name: string;
  description: string;
  strategy_type: string;
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

  // Load strategies on mount
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/strategies");
        const data = await response.json();
        setStrategies(data);

        // If initial strategy is provided and valid, select it
        if (initialStrategy && data.some((s: Strategy) => s.name === initialStrategy)) {
          setSelectedStrategy(initialStrategy);
        }
      } catch (err) {
        console.error("Failed to load strategies:", err);
      }
    };
    loadStrategies();
  }, [initialStrategy]);

  // Check data availability when params change
  useEffect(() => {
    const checkData = async () => {
      if (!symbol || !timeframe) return;

      setCheckingData(true);
      try {
        const params = new URLSearchParams({
          start_date: startDate,
          end_date: endDate,
        });
        const response = await fetch(
          `http://localhost:8000/api/data/check/${symbol}/${timeframe}?${params}`
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
  }, [symbol, timeframe, startDate, endDate]);

  const handleRunBacktest = async () => {
    if (!selectedStrategy) {
      setError("Please select a strategy");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/backtest", {
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
    } catch (err) {
      setError(`Backtest failed: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-neutral-800">
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

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Configuration</CardTitle>
                <CardDescription>
                  Select strategy and data parameters
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Strategy Selection */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Strategy</label>
                  <select
                    value={selectedStrategy}
                    onChange={(e) => setSelectedStrategy(e.target.value)}
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
                  >
                    <option value="">Select a strategy...</option>
                    {strategies.map((s) => (
                      <option key={s.name} value={s.name}>
                        {s.name} ({s.strategy_type})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Symbol */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Symbol</label>
                  <input
                    type="text"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
                    placeholder="BTCUSDT"
                  />
                </div>

                {/* Timeframe */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Timeframe</label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
                  >
                    <option value="1h">1 hour</option>
                    <option value="4h">4 hours</option>
                    <option value="1d">1 day</option>
                  </select>
                </div>

                {/* Date Range */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Start Date</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">End Date</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
                    />
                  </div>
                </div>

                {/* Initial Capital */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Initial Capital ($)</label>
                  <input
                    type="number"
                    value={initialCapital}
                    onChange={(e) => setInitialCapital(Number(e.target.value))}
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
                    min={100}
                    step={1000}
                  />
                </div>

                {/* Data Availability Check */}
                <div className="rounded-lg border p-3">
                  <div className="flex items-center gap-2">
                    {checkingData ? (
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                    ) : dataAvailable === true ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : dataAvailable === false ? (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-neutral-400" />
                    )}
                    <span className="text-sm">
                      {checkingData
                        ? "Checking data..."
                        : dataAvailable === true
                        ? "Data available"
                        : dataAvailable === false
                        ? "Data not available"
                        : "Unknown data status"}
                    </span>
                  </div>
                  {dataAvailable === false && (
                    <Link href="/data" className="text-xs text-blue-600 hover:underline mt-1 block">
                      Go to Data Management to fetch data
                    </Link>
                  )}
                </div>

                {/* Run Button */}
                <Button
                  onClick={handleRunBacktest}
                  disabled={loading || !selectedStrategy || dataAvailable === false}
                  className="w-full"
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

                {/* Error Display */}
                {error && (
                  <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
                    {error}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {result ? (
              <div className="space-y-6">
                {/* Metrics Cards */}
                <div className="grid gap-4 md:grid-cols-3">
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
                </div>

                <div className="grid gap-4 md:grid-cols-3">
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
                    <EquityCurveChart
                      data={result.equity_curve}
                      initialCapital={initialCapital}
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
                        <thead className="sticky top-0 bg-white dark:bg-neutral-900">
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
              <Card className="h-full flex items-center justify-center py-20">
                <CardContent className="text-center">
                  <BarChart3 className="mx-auto h-16 w-16 text-neutral-300 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Results Yet</h3>
                  <p className="text-neutral-600 dark:text-neutral-400">
                    Configure parameters and run a backtest to see results
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
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

function EquityCurveChart({
  data,
  initialCapital
}: {
  data: { time: string; value: number }[];
  initialCapital: number;
}) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-neutral-400">
        No equity curve data
      </div>
    );
  }

  // Simple SVG line chart
  const values = data.map((d) => d.value);
  const minValue = Math.min(...values) * 0.95;
  const maxValue = Math.max(...values) * 1.05;
  const range = maxValue - minValue;

  const width = 800;
  const height = 256;
  const padding = 40;

  const points = data.map((d, index) => {
    const x = padding + (index / (data.length - 1)) * (width - padding * 2);
    const y = height - padding - ((d.value - minValue) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(" ");

  // Determine color based on final value vs initial
  const finalValue = values[values.length - 1];
  const isProfit = finalValue >= initialCapital;
  const lineColor = isProfit ? "#22c55e" : "#ef4444";
  const fillColor = isProfit ? "rgba(34, 197, 94, 0.1)" : "rgba(239, 68, 68, 0.1)";

  // Create fill polygon
  const fillPoints = `${padding},${height - padding} ${points} ${width - padding},${height - padding}`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-64">
      {/* Grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map((pct) => (
        <line
          key={pct}
          x1={padding}
          y1={padding + pct * (height - padding * 2)}
          x2={width - padding}
          y2={padding + pct * (height - padding * 2)}
          stroke="#e5e5e5"
          strokeDasharray="4"
        />
      ))}

      {/* Initial capital reference line */}
      <line
        x1={padding}
        y1={height - padding - ((initialCapital - minValue) / range) * (height - padding * 2)}
        x2={width - padding}
        y2={height - padding - ((initialCapital - minValue) / range) * (height - padding * 2)}
        stroke="#94a3b8"
        strokeDasharray="8"
        strokeWidth="1"
      />

      {/* Fill area */}
      <polygon points={fillPoints} fill={fillColor} />

      {/* Line */}
      <polyline
        points={points}
        fill="none"
        stroke={lineColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Y-axis labels */}
      <text x={padding - 5} y={padding} fontSize="10" textAnchor="end" fill="#666">
        ${maxValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
      </text>
      <text x={padding - 5} y={height - padding} fontSize="10" textAnchor="end" fill="#666">
        ${minValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
      </text>
      <text
        x={padding - 5}
        y={height - padding - ((initialCapital - minValue) / range) * (height - padding * 2)}
        fontSize="10"
        textAnchor="end"
        fill="#94a3b8"
      >
        ${initialCapital.toLocaleString()}
      </text>

      {/* Start/End labels */}
      <text x={padding} y={height - 10} fontSize="10" textAnchor="start" fill="#666">
        Start
      </text>
      <text x={width - padding} y={height - 10} fontSize="10" textAnchor="end" fill="#666">
        End
      </text>
    </svg>
  );
}

export default function BacktestPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    }>
      <BacktestPageContent />
    </Suspense>
  );
}
