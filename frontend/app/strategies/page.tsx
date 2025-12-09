"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { ArrowLeft, Plus, PlayCircle, Settings, Layers, Zap, RefreshCw, Trash2 } from "lucide-react";
import Link from "next/link";

interface Strategy {
  name: string;
  description: string;
  strategy_type: string;  // Class name (e.g., "MovingAverageCrossover") or "composite"
  parameters: Record<string, any>;
  regime_filter: string[] | null;
  sub_regime_filter: Record<string, string[]> | null;
}

// Strategy type badge colors
const TYPE_COLORS: Record<string, string> = {
  builtin: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200",
  composite: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200",
};

// Default color for class-based strategies
const DEFAULT_TYPE_COLOR = "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200";

// Regime badge colors
const REGIME_COLORS: Record<string, string> = {
  TREND_UP: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200",
  TREND_DOWN: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200",
  RANGE: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200",
  CHOPPY: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200",
  NEUTRAL: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200",
};

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingStrategy, setDeletingStrategy] = useState<string | null>(null);

  const loadStrategies = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("http://localhost:8000/api/strategies");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStrategies(data);
    } catch (err) {
      setError(`Failed to load strategies: ${err}`);
      setStrategies([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStrategies();
  }, []);

  const handleDeleteStrategy = async (name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    setDeletingStrategy(name);
    try {
      const response = await fetch(`http://localhost:8000/api/strategies/${encodeURIComponent(name)}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`Failed to delete strategy`);
      }
      await loadStrategies();
    } catch (err) {
      setError(`Failed to delete strategy: ${err}`);
    } finally {
      setDeletingStrategy(null);
    }
  };

  // Separate strategies by type
  // Composite strategies have strategy_type === "composite"
  // Built-in strategies have class names (e.g., "MovingAverageCrossover")
  const compositeStrategies = strategies.filter((s) => s.strategy_type === "composite");
  const builtinStrategies = strategies.filter((s) => s.strategy_type !== "composite");

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-neutral-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="outline" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold">Strategy Portfolio</h1>
              <p className="text-neutral-600 dark:text-neutral-400">
                Manage and test your trading strategies
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadStrategies} disabled={loading}>
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Link href="/strategies/create">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Strategy
              </Button>
            </Link>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          </div>
        )}

        {/* Empty State */}
        {!loading && strategies.length === 0 && !error && (
          <Card className="text-center py-12">
            <CardContent>
              <Layers className="mx-auto h-12 w-12 text-neutral-400 mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Strategies Found</h3>
              <p className="text-neutral-600 dark:text-neutral-400 mb-4">
                Get started by creating your first trading strategy
              </p>
              <Link href="/strategies/create">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Strategy
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {/* Built-in Strategies Section */}
        {!loading && builtinStrategies.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="h-5 w-5 text-blue-600" />
              <h2 className="text-xl font-semibold">Built-in Strategies</h2>
              <span className="text-sm text-neutral-500">({builtinStrategies.length})</span>
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {builtinStrategies.map((strategy) => (
                <StrategyCard
                  key={strategy.name}
                  strategy={strategy}
                  onDelete={handleDeleteStrategy}
                  isDeleting={deletingStrategy === strategy.name}
                />
              ))}
            </div>
          </div>
        )}

        {/* Composite Strategies Section */}
        {!loading && compositeStrategies.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Layers className="h-5 w-5 text-purple-600" />
              <h2 className="text-xl font-semibold">Custom Strategies</h2>
              <span className="text-sm text-neutral-500">({compositeStrategies.length})</span>
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {compositeStrategies.map((strategy) => (
                <StrategyCard
                  key={strategy.name}
                  strategy={strategy}
                  onDelete={handleDeleteStrategy}
                  isDeleting={deletingStrategy === strategy.name}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StrategyCard({
  strategy,
  onDelete,
  isDeleting,
}: {
  strategy: Strategy;
  onDelete: (name: string) => void;
  isDeleting: boolean;
}) {
  return (
    <Card className="flex flex-col hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{strategy.name}</CardTitle>
            <div className="flex gap-2 mt-2">
              <span className={`px-2 py-0.5 text-xs font-medium rounded ${TYPE_COLORS[strategy.strategy_type] || DEFAULT_TYPE_COLOR}`}>
                {strategy.strategy_type}
              </span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 pb-3">
        <CardDescription className="text-sm line-clamp-2 mb-3">
          {strategy.description || "No description"}
        </CardDescription>

        {/* Parameters */}
        {strategy.parameters && Object.keys(strategy.parameters).length > 0 && (
          <div className="mb-3">
            <h4 className="text-xs font-medium text-neutral-500 uppercase mb-1">Parameters</h4>
            <div className="flex flex-wrap gap-1">
              {Object.entries(strategy.parameters).slice(0, 3).map(([key, value]) => (
                <span
                  key={key}
                  className="px-2 py-0.5 text-xs bg-neutral-100 dark:bg-neutral-700 rounded"
                >
                  {key}: {String(value)}
                </span>
              ))}
              {Object.keys(strategy.parameters).length > 3 && (
                <span className="px-2 py-0.5 text-xs text-neutral-500">
                  +{Object.keys(strategy.parameters).length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Regime Filter */}
        {strategy.regime_filter && strategy.regime_filter.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-neutral-500 uppercase mb-1">Regime Filter</h4>
            <div className="flex flex-wrap gap-1">
              {strategy.regime_filter.map((regime) => (
                <span
                  key={regime}
                  className={`px-2 py-0.5 text-xs font-medium rounded ${REGIME_COLORS[regime] || "bg-gray-100 text-gray-700"}`}
                >
                  {regime}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="pt-3 border-t gap-2">
        <Link href={`/backtest?strategy=${encodeURIComponent(strategy.name)}`} className="flex-1">
          <Button variant="default" size="sm" className="w-full">
            <PlayCircle className="mr-2 h-4 w-4" />
            Backtest
          </Button>
        </Link>
        <Button variant="outline" size="icon" title="Settings" disabled>
          <Settings className="h-4 w-4" />
        </Button>
        {strategy.strategy_type === "composite" && (
          <Button
            variant="outline"
            size="icon"
            title="Delete"
            onClick={() => onDelete(strategy.name)}
            disabled={isDeleting}
            className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-950"
          >
            {isDeleting ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-red-600 border-t-transparent" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
