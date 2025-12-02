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

export default function ChartPage() {
  const params = useParams();
  const router = useRouter();
  const symbol = params.symbol as string;
  const timeframe = params.timeframe as string;

  const [candles, setCandles] = useState<CandleData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCandles = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `http://localhost:8000/api/data/candles/${symbol}/${timeframe}`
        );

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`No data found for ${symbol} ${timeframe}`);
          }
          throw new Error(`Failed to fetch candles: ${response.statusText}`);
        }

        const data = await response.json();
        setCandles(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load chart data");
      } finally {
        setLoading(false);
      }
    };

    if (symbol && timeframe) {
      fetchCandles();
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
              <CandlestickChart
                data={candles}
                symbol={symbol}
                timeframe={timeframe}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
