'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiEndpoint } from '@/lib/config';

interface ReportSummary {
  id: string;
  strategy_name: string;
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  total_return_pct: number | null;
  sharpe_ratio: number | null;
  total_trades: number;
  created_at: string;
}

interface ReportDetail {
  id: string;
  strategy_name: string;
  strategy_config: Record<string, unknown>;
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  total_trades: number;
  profit_factor: number;
  equity_curve: Array<{ time: string; value: number }>;
  trades: Array<{
    entry_time: string;
    exit_time: string;
    entry_price: number;
    exit_price: number;
    pnl: number;
    pnl_pct: number;
  }>;
  ai_summary: string | null;
  ai_recommendations: string[];
  ai_concerns: string[];
  created_at: string;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString();
}

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '-';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function getReturnColor(value: number | null): string {
  if (value === null) return 'text-neutral-400';
  return value >= 0 ? 'text-green-400' : 'text-red-400';
}

function getSharpeColor(value: number | null): string {
  if (value === null) return 'text-neutral-400';
  if (value >= 2) return 'text-green-400';
  if (value >= 1) return 'text-yellow-400';
  return 'text-red-400';
}

interface Filters {
  symbol: string;
  timeframe: string;
  strategy: string;
  period: string;
}

export default function ResultsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [selectedReport, setSelectedReport] = useState<ReportDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>({
    symbol: '',
    timeframe: '',
    strategy: '',
    period: '',
  });

  // Extract unique values for filter options
  const uniqueSymbols = [...new Set(reports.map(r => r.symbol))].sort();
  const uniqueTimeframes = [...new Set(reports.map(r => r.timeframe))].sort();
  const uniqueStrategies = [...new Set(reports.map(r => r.strategy_name))].sort();
  const uniquePeriods = [...new Set(reports.map(r => `${r.start_date}|${r.end_date}`))].sort();

  // Apply filters
  const filteredReports = reports.filter(report => {
    if (filters.symbol && report.symbol !== filters.symbol) return false;
    if (filters.timeframe && report.timeframe !== filters.timeframe) return false;
    if (filters.strategy && report.strategy_name !== filters.strategy) return false;
    if (filters.period) {
      const reportPeriod = `${report.start_date}|${report.end_date}`;
      if (reportPeriod !== filters.period) return false;
    }
    return true;
  });

  const activeFiltersCount = Object.values(filters).filter(Boolean).length;

  const clearFilters = () => {
    setFilters({ symbol: '', timeframe: '', strategy: '', period: '' });
  };

  const FilterSelect = ({
    label,
    value,
    options,
    onChange,
    formatOption
  }: {
    label: string;
    value: string;
    options: string[];
    onChange: (val: string) => void;
    formatOption?: (opt: string) => string;
  }) => (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`px-2 py-1 text-xs rounded border transition-colors bg-neutral-800 ${
        value ? 'border-purple-500 text-white' : 'border-neutral-600 text-neutral-400'
      }`}
    >
      <option value="">{label}</option>
      {options.map(opt => (
        <option key={opt} value={opt}>
          {formatOption ? formatOption(opt) : opt}
        </option>
      ))}
    </select>
  );

  const formatPeriodOption = (period: string) => {
    const [start, end] = period.split('|');
    return `${formatDate(start)} - ${formatDate(end)}`;
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      setError(null);
      const response = await fetch(apiEndpoint('/reports'));
      if (!response.ok) throw new Error('Failed to fetch reports');
      const data = await response.json();
      setReports(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchReportDetail = async (reportId: string) => {
    try {
      setError(null);
      const response = await fetch(apiEndpoint(`/reports/${reportId}`));
      if (!response.ok) throw new Error('Failed to fetch report');
      const data = await response.json();
      setSelectedReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load report');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-neutral-400 hover:text-white text-sm">
            &larr; Back
          </Link>
          <h1 className="text-2xl font-bold text-white">Backtest Reports</h1>
        </div>
        <Link
          href="/chat"
          className="text-sm px-4 py-2 rounded bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
        >
          New Analysis
        </Link>
      </div>

      <div>
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin h-8 w-8 border-2 border-purple-500 border-t-transparent rounded-full" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-400 mb-4">{error}</p>
            <button
              onClick={fetchReports}
              className="px-4 py-2 rounded bg-neutral-800 hover:bg-neutral-700 text-white"
            >
              Retry
            </button>
          </div>
        ) : reports.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📭</div>
            <h2 className="text-xl font-semibold mb-2">No reports yet</h2>
            <p className="text-neutral-400 mb-6">
              Run a backtest with the research agent to save reports here.
            </p>
            <Link
              href="/chat"
              className="inline-block px-4 py-2 rounded bg-primary hover:bg-primary/80 text-primary-foreground font-medium"
            >
              Start Research
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Filters bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 bg-neutral-800 rounded-lg p-4 border border-neutral-700">
              <div className="flex flex-wrap items-center gap-2">
                <FilterSelect
                  label="Ticker"
                  value={filters.symbol}
                  options={uniqueSymbols}
                  onChange={(val) => setFilters(f => ({ ...f, symbol: val }))}
                />
                <FilterSelect
                  label="Timeframe"
                  value={filters.timeframe}
                  options={uniqueTimeframes}
                  onChange={(val) => setFilters(f => ({ ...f, timeframe: val }))}
                />
                <FilterSelect
                  label="Strategy"
                  value={filters.strategy}
                  options={uniqueStrategies}
                  onChange={(val) => setFilters(f => ({ ...f, strategy: val }))}
                />
                <FilterSelect
                  label="Period"
                  value={filters.period}
                  options={uniquePeriods}
                  onChange={(val) => setFilters(f => ({ ...f, period: val }))}
                  formatOption={formatPeriodOption}
                />
                {activeFiltersCount > 0 && (
                  <button
                    onClick={clearFilters}
                    className="px-2 py-1 text-xs text-neutral-400 hover:text-white"
                  >
                    Clear
                  </button>
                )}
              </div>
              <span className="text-sm text-neutral-400">
                {filteredReports.length} / {reports.length}
              </span>
            </div>

            {/* Reports grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredReports.map((report) => (
                <button
                  key={report.id}
                  onClick={() => fetchReportDetail(report.id)}
                  className={`text-left p-4 rounded-lg border transition-colors ${
                    selectedReport?.id === report.id
                      ? 'bg-neutral-700 border-purple-500'
                      : 'bg-neutral-800 border-neutral-700 hover:border-neutral-600'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="font-medium truncate text-sm">{report.strategy_name}</span>
                    <span className={`text-sm font-semibold ${getReturnColor(report.total_return_pct)}`}>
                      {formatPercent(report.total_return_pct)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-neutral-400 mb-1">
                    <span className="font-medium">{report.symbol}</span>
                    <span>&bull;</span>
                    <span>{report.timeframe}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-neutral-500">
                    <span>{report.total_trades} trades</span>
                    <span>{formatDate(report.created_at)}</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Report detail */}
            <div>
              {selectedReport ? (
                <div className="space-y-6">
                  {/* Header */}
                  <div className="bg-neutral-800 rounded-lg p-6 border border-neutral-700">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h2 className="text-xl font-semibold">{selectedReport.strategy_name}</h2>
                        <p className="text-neutral-400 text-sm">
                          {selectedReport.symbol} &bull; {selectedReport.timeframe} &bull;{' '}
                          {formatDate(selectedReport.start_date)} - {formatDate(selectedReport.end_date)}
                        </p>
                      </div>
                      <span className={`text-2xl font-bold ${getReturnColor(selectedReport.total_return_pct)}`}>
                        {formatPercent(selectedReport.total_return_pct)}
                      </span>
                    </div>

                    {/* Metrics grid */}
                    <div className="grid grid-cols-3 sm:grid-cols-6 gap-4">
                      <div>
                        <div className="text-xs text-neutral-400">Sharpe</div>
                        <div className={`text-lg font-semibold ${getSharpeColor(selectedReport.sharpe_ratio)}`}>
                          {selectedReport.sharpe_ratio?.toFixed(2) ?? '-'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-neutral-400">Max DD</div>
                        <div className="text-lg font-semibold text-red-400">
                          {selectedReport.max_drawdown_pct?.toFixed(2) ?? '-'}%
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-neutral-400">Win Rate</div>
                        <div className="text-lg font-semibold">
                          {selectedReport.win_rate_pct?.toFixed(1) ?? '-'}%
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-neutral-400">Profit Factor</div>
                        <div className="text-lg font-semibold">
                          {selectedReport.profit_factor?.toFixed(2) ?? '-'}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-neutral-400">Trades</div>
                        <div className="text-lg font-semibold">{selectedReport.total_trades}</div>
                      </div>
                      <div>
                        <div className="text-xs text-neutral-400">Capital</div>
                        <div className="text-lg font-semibold">
                          ${selectedReport.initial_capital?.toLocaleString() ?? '-'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* AI Analysis */}
                  {(selectedReport.ai_summary || selectedReport.ai_recommendations?.length > 0) && (
                    <div className="bg-neutral-800 rounded-lg p-6 border border-neutral-700">
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <span className="text-purple-400">🤖</span> AI Analysis
                      </h3>

                      {selectedReport.ai_summary && (
                        <p className="text-neutral-300 text-sm mb-4">{selectedReport.ai_summary}</p>
                      )}

                      {selectedReport.ai_recommendations?.length > 0 && (
                        <div className="mb-4">
                          <h4 className="text-sm font-medium text-green-400 mb-2">Recommendations</h4>
                          <ul className="space-y-1">
                            {selectedReport.ai_recommendations.map((rec, i) => (
                              <li key={i} className="text-sm text-neutral-300 flex items-start gap-2">
                                <span className="text-green-400">✓</span>
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {selectedReport.ai_concerns?.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-yellow-400 mb-2">Concerns</h4>
                          <ul className="space-y-1">
                            {selectedReport.ai_concerns.map((concern, i) => (
                              <li key={i} className="text-sm text-neutral-300 flex items-start gap-2">
                                <span className="text-yellow-400">⚠</span>
                                {concern}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Equity curve */}
                  {selectedReport.equity_curve?.length > 0 && (
                    <div className="bg-neutral-800 rounded-lg p-6 border border-neutral-700">
                      <h3 className="font-semibold mb-3">Equity Curve</h3>
                      <div className="h-48 flex items-end gap-px">
                        {selectedReport.equity_curve.slice(-100).map((point, i) => {
                          const values = selectedReport.equity_curve.slice(-100).map(p => p.value);
                          const min = Math.min(...values);
                          const max = Math.max(...values);
                          const range = max - min || 1;
                          const height = ((point.value - min) / range) * 100;
                          const isProfit = point.value >= selectedReport.initial_capital;

                          return (
                            <div
                              key={i}
                              className={`flex-1 rounded-t ${isProfit ? 'bg-green-500/50' : 'bg-red-500/50'}`}
                              style={{ height: `${Math.max(height, 2)}%` }}
                              title={`$${point.value.toFixed(2)}`}
                            />
                          );
                        })}
                      </div>
                      <div className="flex justify-between text-xs text-neutral-500 mt-2">
                        <span>{formatDate(selectedReport.start_date)}</span>
                        <span>{formatDate(selectedReport.end_date)}</span>
                      </div>
                    </div>
                  )}

                  {/* Trades table */}
                  {selectedReport.trades?.length > 0 && (
                    <div className="bg-neutral-800 rounded-lg p-6 border border-neutral-700">
                      <h3 className="font-semibold mb-3">Recent Trades</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-neutral-400 text-xs">
                              <th className="text-left py-2">Entry</th>
                              <th className="text-left py-2">Exit</th>
                              <th className="text-right py-2">Entry Price</th>
                              <th className="text-right py-2">Exit Price</th>
                              <th className="text-right py-2">P&L</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedReport.trades.slice(0, 20).map((trade, i) => (
                              <tr key={i} className="border-t border-neutral-700">
                                <td className="py-2 text-neutral-300">{formatDate(trade.entry_time)}</td>
                                <td className="py-2 text-neutral-300">{formatDate(trade.exit_time)}</td>
                                <td className="py-2 text-right">${trade.entry_price?.toFixed(2)}</td>
                                <td className="py-2 text-right">${trade.exit_price?.toFixed(2)}</td>
                                <td className={`py-2 text-right ${getReturnColor(trade.pnl_pct)}`}>
                                  {formatPercent(trade.pnl_pct)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {selectedReport.trades.length > 20 && (
                          <p className="text-xs text-neutral-500 mt-2">
                            Showing 20 of {selectedReport.trades.length} trades
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 text-neutral-500">
                  Select a report to view details
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
