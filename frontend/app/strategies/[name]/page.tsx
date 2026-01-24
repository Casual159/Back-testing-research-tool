"use client";

import { useState, useEffect, use } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, PlayCircle, Settings, Zap, Layers, AlertCircle } from "lucide-react";
import Link from "next/link";

interface StrategyDetail {
  name: string;
  description: string;
  strategy_type: string;
  builtin_class: string | null;
  parameters: Record<string, any>;
  regime_filter: string[] | null;
  entry_logic: any | null;
  exit_logic: any | null;
  created_at: string | null;
  updated_at: string | null;
}

// Regime badge colors
const REGIME_COLORS: Record<string, string> = {
  TREND_UP: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200",
  TREND_DOWN: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200",
  RANGE: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200",
  CHOPPY: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200",
  NEUTRAL: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200",
};

export default function StrategyDetailPage({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = use(params);
  const [strategy, setStrategy] = useState<StrategyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStrategy = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `http://localhost:8000/api/strategies/${encodeURIComponent(name)}`
        );
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`Strategy "${name}" not found`);
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setStrategy(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    };

    loadStrategy();
  }, [name]);

  const isComposite = strategy?.strategy_type === "composite";

  return (
    <div className="min-h-screen bg-neutral-900">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-8 flex items-center gap-4">
          <Link href="/strategies">
            <Button variant="outline" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">{decodeURIComponent(name)}</h1>
            <p className="text-neutral-600 dark:text-neutral-400">
              Strategy Details
            </p>
          </div>
          {strategy && (
            <Link href={`/backtest?strategy=${encodeURIComponent(strategy.name)}`}>
              <Button>
                <PlayCircle className="mr-2 h-4 w-4" />
                Run Backtest
              </Button>
            </Link>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          </div>
        )}

        {/* Error State */}
        {error && (
          <Card className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950">
            <CardContent className="flex items-center gap-4 py-8">
              <AlertCircle className="h-12 w-12 text-red-600 dark:text-red-400" />
              <div>
                <h3 className="text-lg font-semibold text-red-700 dark:text-red-300">
                  Error Loading Strategy
                </h3>
                <p className="text-red-600 dark:text-red-400">{error}</p>
                <Link href="/strategies" className="mt-2 inline-block">
                  <Button variant="outline" size="sm">
                    Back to Strategies
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Strategy Details */}
        {strategy && !loading && (
          <div className="space-y-6">
            {/* Overview Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  {isComposite ? (
                    <Layers className="h-6 w-6 text-purple-600" />
                  ) : (
                    <Zap className="h-6 w-6 text-blue-600" />
                  )}
                  <CardTitle>Overview</CardTitle>
                  <span
                    className={`px-2 py-0.5 text-xs font-medium rounded ${
                      isComposite
                        ? "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200"
                        : "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200"
                    }`}
                  >
                    {strategy.strategy_type}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Description */}
                <div>
                  <h4 className="text-sm font-medium text-neutral-500 uppercase mb-2">
                    Description
                  </h4>
                  <p className="text-neutral-700 dark:text-neutral-300 whitespace-pre-wrap">
                    {strategy.description || "No description available"}
                  </p>
                </div>

                {/* Timestamps */}
                {(strategy.created_at || strategy.updated_at) && (
                  <div className="flex gap-6 text-sm text-neutral-500">
                    {strategy.created_at && (
                      <div>
                        <span className="font-medium">Created:</span>{" "}
                        {new Date(strategy.created_at).toLocaleDateString()}
                      </div>
                    )}
                    {strategy.updated_at && (
                      <div>
                        <span className="font-medium">Updated:</span>{" "}
                        {new Date(strategy.updated_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Parameters Card */}
            {strategy.parameters && Object.keys(strategy.parameters).length > 0 && (
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <Settings className="h-5 w-5 text-neutral-600" />
                    <CardTitle className="text-lg">Parameters</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {Object.entries(strategy.parameters).map(([key, value]) => (
                      <div
                        key={key}
                        className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900"
                      >
                        <div className="text-xs text-neutral-500 uppercase mb-1">
                          {key.replace(/_/g, " ")}
                        </div>
                        <div className="font-mono text-lg">
                          {typeof value === "boolean"
                            ? value
                              ? "Yes"
                              : "No"
                            : String(value)}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Regime Filter Card */}
            {strategy.regime_filter && strategy.regime_filter.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Regime Filter</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-3">
                    This strategy is designed to trade in the following market regimes:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {strategy.regime_filter.map((regime) => (
                      <span
                        key={regime}
                        className={`px-3 py-1.5 text-sm font-medium rounded-lg ${
                          REGIME_COLORS[regime] || "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {regime}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Entry/Exit Logic for Composite Strategies */}
            {isComposite && (strategy.entry_logic || strategy.exit_logic) && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Trading Logic</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {strategy.entry_logic && (
                    <div>
                      <h4 className="text-sm font-medium text-green-600 dark:text-green-400 uppercase mb-2">
                        Entry Conditions
                      </h4>
                      <pre className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900 text-xs overflow-x-auto">
                        {JSON.stringify(strategy.entry_logic, null, 2)}
                      </pre>
                    </div>
                  )}
                  {strategy.exit_logic && (
                    <div>
                      <h4 className="text-sm font-medium text-red-600 dark:text-red-400 uppercase mb-2">
                        Exit Conditions
                      </h4>
                      <pre className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-900 text-xs overflow-x-auto">
                        {JSON.stringify(strategy.exit_logic, null, 2)}
                      </pre>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            <div className="flex gap-4 pt-4">
              <Link
                href={`/backtest?strategy=${encodeURIComponent(strategy.name)}`}
                className="flex-1"
              >
                <Button className="w-full" size="lg">
                  <PlayCircle className="mr-2 h-5 w-5" />
                  Run Backtest with this Strategy
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
