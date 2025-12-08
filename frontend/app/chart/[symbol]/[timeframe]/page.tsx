"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import CandlestickChart from "@/components/CandlestickChart";

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

export default function ChartPage() {
  const params = useParams();
  const router = useRouter();
  const symbol = params.symbol as string;
  const timeframe = params.timeframe as string;

  const [candles, setCandles] = useState<CandleData[]>([]);
  const [regimeData, setRegimeData] = useState<RegimeData[]>([]);
  const [showRegime, setShowRegime] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch both candles and regime data in parallel
        const [candlesRes, regimeRes] = await Promise.all([
          fetch(`http://localhost:8000/api/data/candles/${symbol}/${timeframe}`),
          fetch(`http://localhost:8000/api/data/regime/${symbol}/${timeframe}`)
        ]);

        if (!candlesRes.ok) {
          if (candlesRes.status === 404) {
            throw new Error(`No data found for ${symbol} ${timeframe}`);
          }
          throw new Error(`Failed to fetch candles: ${candlesRes.statusText}`);
        }

        const candlesData = await candlesRes.json();
        setCandles(candlesData);

        // Regime data is optional - don't fail if not available
        if (regimeRes.ok) {
          const regimeDataRes = await regimeRes.json();
          setRegimeData(regimeDataRes);
        } else {
          console.warn('Regime data not available:', regimeRes.statusText);
          setRegimeData([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load chart data");
      } finally {
        setLoading(false);
      }
    };

    if (symbol && timeframe) {
      fetchData();
    }
  }, [symbol, timeframe]);

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-neutral-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center gap-4">
          <Link href="/data">
            <Button variant="outline" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">
              {symbol} - {timeframe}
            </h1>
            <p className="text-neutral-600 dark:text-neutral-400">
              Candlestick Chart Visualization
            </p>
          </div>
        </div>

        {/* Chart Card */}
        <Card>
          <CardContent className="p-6">
            {loading && (
              <div className="flex items-center justify-center h-96">
                <div className="text-center">
                  <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
                  <p className="text-neutral-600 dark:text-neutral-400">
                    Loading chart data...
                  </p>
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center justify-center h-96">
                <div className="text-center max-w-md">
                  <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950">
                    <h3 className="font-semibold text-red-900 dark:text-red-100">
                      Error Loading Chart
                    </h3>
                    <p className="mt-2 text-sm text-red-700 dark:text-red-300">
                      {error}
                    </p>
                    <Link href="/data">
                      <Button variant="outline" className="mt-4">
                        Back to Data Management
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            )}

            {!loading && !error && candles.length > 0 && (
              <>
                {/* Regime Toggle Control */}
                {regimeData.length > 0 && (
                  <div className="mb-4 flex items-center gap-4">
                    <Button
                      variant={showRegime ? "default" : "outline"}
                      size="sm"
                      onClick={() => setShowRegime(!showRegime)}
                    >
                      {showRegime ? "Hide" : "Show"} Market Regime
                    </Button>
                    {showRegime && (
                      <div className="flex items-center gap-3 text-sm">
                        <span className="text-neutral-600 dark:text-neutral-400">
                          Regime Legend:
                        </span>
                        <div className="flex gap-2">
                          <div className="flex items-center gap-1">
                            <div className="h-3 w-3 rounded" style={{ backgroundColor: "#22c55e" }} />
                            <span>TREND_UP</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="h-3 w-3 rounded" style={{ backgroundColor: "#ef4444" }} />
                            <span>TREND_DOWN</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="h-3 w-3 rounded" style={{ backgroundColor: "#3b82f6" }} />
                            <span>RANGE</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="h-3 w-3 rounded" style={{ backgroundColor: "#f59e0b" }} />
                            <span>CHOPPY</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <div className="h-3 w-3 rounded" style={{ backgroundColor: "#6b7280" }} />
                            <span>NEUTRAL</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <CandlestickChart
                  data={candles}
                  symbol={symbol}
                  timeframe={timeframe}
                  regimeData={regimeData}
                  showRegime={showRegime}
                />
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
