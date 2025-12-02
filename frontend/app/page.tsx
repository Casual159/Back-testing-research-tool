import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, TrendingUp, Settings, BarChart3 } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-neutral-800">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="mb-4 text-5xl font-bold tracking-tight">
            Backtesting Research Tool
          </h1>
          <p className="text-xl text-neutral-600 dark:text-neutral-400">
            AI-Enhanced Cryptocurrency Trading Strategy Research Platform
          </p>
        </div>

        {/* Main Cards Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2 mb-12">
          {/* Data Management Card */}
          <Link href="/data">
            <Card className="cursor-pointer transition-all hover:shadow-lg hover:scale-105">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Database className="h-6 w-6 text-blue-600" />
                  <CardTitle>Data Management</CardTitle>
                </div>
                <CardDescription>
                  Fetch and manage historical data from Binance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  Download OHLCV data, view database statistics, and manage your data storage.
                </p>
              </CardContent>
            </Card>
          </Link>

          {/* Backtesting Card */}
          <Link href="/backtest">
            <Card className="cursor-pointer transition-all hover:shadow-lg hover:scale-105">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-6 w-6 text-green-600" />
                  <CardTitle>Run Backtest</CardTitle>
                </div>
                <CardDescription>
                  Test your trading strategies on historical data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  Execute backtests with various strategies and analyze performance metrics.
                </p>
              </CardContent>
            </Card>
          </Link>

          {/* Results Card */}
          <Link href="/results">
            <Card className="cursor-pointer transition-all hover:shadow-lg hover:scale-105">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-6 w-6 text-purple-600" />
                  <CardTitle>Results</CardTitle>
                </div>
                <CardDescription>
                  View backtest results and performance metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  Analyze returns, Sharpe ratio, drawdowns, and detailed trade history.
                </p>
              </CardContent>
            </Card>
          </Link>

          {/* Strategies Card */}
          <Link href="/strategies">
            <Card className="cursor-pointer transition-all hover:shadow-lg hover:scale-105">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Settings className="h-6 w-6 text-orange-600" />
                  <CardTitle>Strategies</CardTitle>
                </div>
                <CardDescription>
                  Browse and configure trading strategies
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  Explore built-in strategies: RSI, MACD, Bollinger Bands, and more.
                </p>
              </CardContent>
            </Card>
          </Link>
        </div>

        {/* Quick Stats Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
            <CardDescription>Overview of your backtesting environment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
                  Available Strategies
                </div>
                <div className="mt-2 text-3xl font-bold">5</div>
                <p className="mt-1 text-xs text-neutral-500">
                  RSI, MACD, Bollinger Bands, MA Crossover
                </p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
                  Database Status
                </div>
                <div className="mt-2 text-3xl font-bold text-green-600">Active</div>
                <p className="mt-1 text-xs text-neutral-500">
                  PostgreSQL connected
                </p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="text-sm font-medium text-neutral-600 dark:text-neutral-400">
                  API Status
                </div>
                <div className="mt-2 text-3xl font-bold text-blue-600">Ready</div>
                <p className="mt-1 text-xs text-neutral-500">
                  FastAPI backend running
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-neutral-500">
          <p>Built with Next.js, FastAPI, and PostgreSQL</p>
          <p className="mt-2">
            Core backtesting engine powered by battle-tested Python components
          </p>
        </div>
      </div>
    </div>
  );
}
