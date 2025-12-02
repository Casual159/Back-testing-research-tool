"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Download, Database, Calendar, X, LineChart, Trash2 } from "lucide-react";
import Link from "next/link";

interface DataStats {
  symbol: string;
  timeframe: string;
  candle_count: number;
  first_candle: string;
  last_candle: string;
}

export default function DataPage() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1h");
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [stats, setStats] = useState<DataStats[]>([]);
  const [statsLoading, setStatsLoading] = useState(false);
  const [deletingDataset, setDeletingDataset] = useState<string | null>(null);

  // Function to set end date to latest possible (2 days ago)
  const setLatestEndDate = () => {
    const today = new Date();
    today.setDate(today.getDate() - 2); // Binance Public Data has 2-day lag
    const latestDate = today.toISOString().split('T')[0];
    setEndDate(latestDate);
  };

  // Function to load database stats
  const loadStats = async () => {
    setStatsLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/data/stats");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Failed to load stats:", error);
      setStats([]);
    } finally {
      setStatsLoading(false);
    }
  };

  // Load stats on component mount
  useEffect(() => {
    loadStats();
  }, []);

  const handleFetchData = async () => {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/data/fetch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          symbol,
          timeframe,
          start_date: startDate,
          end_date: endDate,
        }),
      });

      const data = await response.json();
      setResult(data);

      // Auto-refresh stats after successful fetch
      if (data.success) {
        await loadStats();
      }
    } catch (error) {
      setResult({
        success: false,
        message: `Error: ${error}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDataset = async (symbol: string, timeframe: string) => {
    const key = `${symbol}-${timeframe}`;
    setDeletingDataset(key);

    try {
      const response = await fetch(
        `http://localhost:8000/api/data/${symbol}/${timeframe}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        await loadStats(); // Refresh stats after deletion
        setResult({
          success: true,
          message: `Successfully deleted ${symbol} ${timeframe}`,
        });
      } else {
        throw new Error("Failed to delete dataset");
      }
    } catch (error) {
      setResult({
        success: false,
        message: `Error deleting dataset: ${error}`,
      });
    } finally {
      setDeletingDataset(null);
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
            <h1 className="text-3xl font-bold">Data Management</h1>
            <p className="text-neutral-600 dark:text-neutral-400">
              Fetch historical data from Binance and store in PostgreSQL
            </p>
          </div>
        </div>

        {/* Fetch Data Form */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Download className="h-5 w-5 text-blue-600" />
              <CardTitle>Fetch Historical Data</CardTitle>
            </div>
            <CardDescription>
              Download OHLCV candles from Binance Public Data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6">
              {/* Form Fields */}
              <div className="grid gap-4 md:grid-cols-2">
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

                <div className="space-y-2">
                  <label className="text-sm font-medium">Timeframe</label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
                  >
                    <option value="1m">1 minute</option>
                    <option value="5m">5 minutes</option>
                    <option value="15m">15 minutes</option>
                    <option value="1h">1 hour</option>
                    <option value="4h">4 hours</option>
                    <option value="1d">1 day</option>
                  </select>
                </div>

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
                  <div className="flex gap-2">
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="flex-1 rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      onClick={setLatestEndDate}
                      title="Set to latest available date (2 days ago)"
                      className="shrink-0"
                    >
                      <Calendar className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Fetch Button */}
              <Button
                onClick={handleFetchData}
                disabled={loading}
                className="w-full md:w-auto"
              >
                {loading ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    Fetch Data
                  </>
                )}
              </Button>

              {/* Result Display */}
              {result && (
                <div
                  className={`relative rounded-lg border p-4 ${
                    result.success
                      ? "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950"
                      : "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
                  }`}
                >
                  <button
                    onClick={() => setResult(null)}
                    className={`absolute top-2 right-2 p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors ${
                      result.success ? "text-green-700 dark:text-green-300" : "text-red-700 dark:text-red-300"
                    }`}
                    title="Close"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <h3
                    className={`font-semibold ${
                      result.success ? "text-green-900 dark:text-green-100" : "text-red-900 dark:text-red-100"
                    }`}
                  >
                    {result.success ? "Success!" : "Error"}
                  </h3>
                  <p
                    className={`mt-1 text-sm ${
                      result.success ? "text-green-700 dark:text-green-300" : "text-red-700 dark:text-red-300"
                    }`}
                  >
                    {result.message}
                  </p>
                  {result.success && (
                    <div className="mt-2 text-sm text-green-700 dark:text-green-300">
                      <p>Candles fetched: {result.candles_fetched}</p>
                      <p>Candles inserted: {result.candles_inserted}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Database Stats */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-purple-600" />
                <CardTitle>Database Statistics</CardTitle>
              </div>
              <Button
                variant="outline"
                onClick={loadStats}
                disabled={statsLoading}
                size="sm"
              >
                {statsLoading ? (
                  <>
                    <div className="mr-2 h-3 w-3 animate-spin rounded-full border-2 border-neutral-600 border-t-transparent" />
                    Loading...
                  </>
                ) : (
                  "Refresh"
                )}
              </Button>
            </div>
            <CardDescription>
              Overview of stored data in PostgreSQL
            </CardDescription>
          </CardHeader>
          <CardContent>
            {stats.length === 0 ? (
              <div className="rounded-lg border p-8 text-center text-neutral-600 dark:text-neutral-400">
                <Database className="mx-auto h-12 w-12 mb-3 opacity-50" />
                <p className="text-sm">No data in database yet</p>
                <p className="text-xs mt-1">Click "Refresh" to check for data</p>
              </div>
            ) : (
              <div className="space-y-3">
                {stats.map((stat, index) => (
                  <div
                    key={index}
                    className="rounded-lg border p-4 hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-semibold text-lg">
                            {stat.symbol}
                          </span>
                          <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200">
                            {stat.timeframe}
                          </span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                          <div>
                            <span className="text-neutral-600 dark:text-neutral-400">
                              Candles:
                            </span>{" "}
                            <span className="font-medium">
                              {stat.candle_count.toLocaleString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-neutral-600 dark:text-neutral-400">
                              From:
                            </span>{" "}
                            <span className="font-medium">
                              {new Date(stat.first_candle).toLocaleDateString()}
                            </span>
                          </div>
                          <div>
                            <span className="text-neutral-600 dark:text-neutral-400">
                              To:
                            </span>{" "}
                            <span className="font-medium">
                              {new Date(stat.last_candle).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Link href={`/chart/${stat.symbol}/${stat.timeframe}`}>
                          <Button variant="outline" size="sm">
                            <LineChart className="mr-2 h-4 w-4" />
                            View Chart
                          </Button>
                        </Link>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteDataset(stat.symbol, stat.timeframe)}
                          disabled={deletingDataset === `${stat.symbol}-${stat.timeframe}`}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-950"
                        >
                          {deletingDataset === `${stat.symbol}-${stat.timeframe}` ? (
                            <>
                              <div className="mr-2 h-3 w-3 animate-spin rounded-full border-2 border-red-600 border-t-transparent" />
                              Deleting...
                            </>
                          ) : (
                            <>
                              <Trash2 className="h-4 w-4" />
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
