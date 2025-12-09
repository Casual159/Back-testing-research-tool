"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Plus, Trash2, Save, Eye, AlertCircle } from "lucide-react";
import Link from "next/link";

// Available indicators with their parameters and outputs
const INDICATORS = {
  RSI: {
    name: "RSI",
    description: "Relative Strength Index",
    parameters: { period: 14 },
    outputs: ["value"],
    defaultCondition: { operator: "<", value: 30 },
  },
  MACD: {
    name: "MACD",
    description: "Moving Average Convergence Divergence",
    parameters: { fast_period: 12, slow_period: 26, signal_period: 9 },
    outputs: ["macd", "signal", "histogram"],
    defaultCondition: { operator: "cross_above", value: "signal" },
  },
  SMA: {
    name: "SMA",
    description: "Simple Moving Average",
    parameters: { period: 20 },
    outputs: ["value"],
    defaultCondition: { operator: "cross_above", value: "price" },
  },
  EMA: {
    name: "EMA",
    description: "Exponential Moving Average",
    parameters: { period: 20 },
    outputs: ["value"],
    defaultCondition: { operator: "cross_above", value: "price" },
  },
  BB: {
    name: "BB",
    description: "Bollinger Bands",
    parameters: { period: 20, num_std: 2.0 },
    outputs: ["upper", "middle", "lower"],
    defaultCondition: { operator: "<", value: "lower" },
  },
};

const CONDITION_OPERATORS = [
  { value: "<", label: "Less than" },
  { value: ">", label: "Greater than" },
  { value: "<=", label: "Less than or equal" },
  { value: ">=", label: "Greater than or equal" },
  { value: "==", label: "Equal to" },
  { value: "cross_above", label: "Crosses above" },
  { value: "cross_below", label: "Crosses below" },
];

const REGIMES = ["TREND_UP", "TREND_DOWN", "RANGE", "CHOPPY", "NEUTRAL"];

interface Signal {
  id: string;
  name: string;
  indicator: string;
  parameters: Record<string, number>;
  condition: {
    operator: string;
    value: number | string;
  };
  indicator_component?: string;
}

export default function CreateStrategyPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [entrySignals, setEntrySignals] = useState<Signal[]>([createDefaultSignal("entry")]);
  const [entryOperator, setEntryOperator] = useState<"AND" | "OR">("AND");
  const [exitSignals, setExitSignals] = useState<Signal[]>([createDefaultExitSignal()]);
  const [exitOperator, setExitOperator] = useState<"AND" | "OR">("AND");
  const [regimeFilter, setRegimeFilter] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  function createDefaultSignal(type: string): Signal {
    return {
      id: crypto.randomUUID(),
      name: `${type}_rsi`,
      indicator: "RSI",
      parameters: { period: 14 },
      condition: { operator: "<", value: 30 },
    };
  }

  function createDefaultExitSignal(): Signal {
    return {
      id: crypto.randomUUID(),
      name: "exit_rsi",
      indicator: "RSI",
      parameters: { period: 14 },
      condition: { operator: ">", value: 70 },
    };
  }

  function updateSignal(signals: Signal[], setSignals: React.Dispatch<React.SetStateAction<Signal[]>>, id: string, updates: Partial<Signal>) {
    setSignals(signals.map(s => s.id === id ? { ...s, ...updates } : s));
  }

  function addSignal(signals: Signal[], setSignals: React.Dispatch<React.SetStateAction<Signal[]>>, type: string) {
    setSignals([...signals, type === "entry" ? createDefaultSignal(type) : createDefaultExitSignal()]);
  }

  function removeSignal(signals: Signal[], setSignals: React.Dispatch<React.SetStateAction<Signal[]>>, id: string) {
    if (signals.length > 1) {
      setSignals(signals.filter(s => s.id !== id));
    }
  }

  function buildLogicTree(signals: Signal[], operator: "AND" | "OR") {
    if (signals.length === 1) {
      return {
        signal: {
          name: signals[0].name,
          indicator: signals[0].indicator,
          parameters: signals[0].parameters,
          condition: signals[0].condition,
          ...(signals[0].indicator_component ? { indicator_component: signals[0].indicator_component } : {}),
        },
      };
    }

    return {
      operator,
      children: signals.map(s => ({
        signal: {
          name: s.name,
          indicator: s.indicator,
          parameters: s.parameters,
          condition: s.condition,
          ...(s.indicator_component ? { indicator_component: s.indicator_component } : {}),
        },
      })),
    };
  }

  async function handleCreate() {
    if (!name.trim()) {
      setError("Strategy name is required");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        name: name.trim(),
        description: description.trim(),
        entry_logic: buildLogicTree(entrySignals, entryOperator),
        exit_logic: buildLogicTree(exitSignals, exitOperator),
        ...(regimeFilter.length > 0 ? { regime_filter: regimeFilter } : {}),
      };

      const response = await fetch("http://localhost:8000/api/strategies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to create strategy");
      }

      router.push("/strategies");
    } catch (err) {
      setError(`Failed to create strategy: ${err}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-neutral-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/strategies">
              <Button variant="outline" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold">Create Strategy</h1>
              <p className="text-neutral-600 dark:text-neutral-400">
                Build a custom composite trading strategy
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowPreview(!showPreview)}>
              <Eye className="mr-2 h-4 w-4" />
              {showPreview ? "Hide" : "Show"} Preview
            </Button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300 flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            {error}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info */}
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Strategy Name *</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900"
                    placeholder="My RSI Strategy"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Description</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full rounded-md border border-neutral-300 px-3 py-2 dark:border-neutral-700 dark:bg-neutral-900 h-20"
                    placeholder="Describe what this strategy does..."
                  />
                </div>
              </CardContent>
            </Card>

            {/* Entry Logic */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-green-600">Entry Logic</CardTitle>
                    <CardDescription>When to open a position</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addSignal(entrySignals, setEntrySignals, "entry")}
                  >
                    <Plus className="mr-1 h-4 w-4" />
                    Add Condition
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {entrySignals.length > 1 && (
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-sm">Combine conditions with:</span>
                    <select
                      value={entryOperator}
                      onChange={(e) => setEntryOperator(e.target.value as "AND" | "OR")}
                      className="rounded-md border border-neutral-300 px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-900"
                    >
                      <option value="AND">AND (all must be true)</option>
                      <option value="OR">OR (any can be true)</option>
                    </select>
                  </div>
                )}
                {entrySignals.map((signal, idx) => (
                  <SignalBuilder
                    key={signal.id}
                    signal={signal}
                    onChange={(updates) => updateSignal(entrySignals, setEntrySignals, signal.id, updates)}
                    onRemove={() => removeSignal(entrySignals, setEntrySignals, signal.id)}
                    canRemove={entrySignals.length > 1}
                    index={idx}
                  />
                ))}
              </CardContent>
            </Card>

            {/* Exit Logic */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-red-600">Exit Logic</CardTitle>
                    <CardDescription>When to close a position</CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addSignal(exitSignals, setExitSignals, "exit")}
                  >
                    <Plus className="mr-1 h-4 w-4" />
                    Add Condition
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {exitSignals.length > 1 && (
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-sm">Combine conditions with:</span>
                    <select
                      value={exitOperator}
                      onChange={(e) => setExitOperator(e.target.value as "AND" | "OR")}
                      className="rounded-md border border-neutral-300 px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-900"
                    >
                      <option value="AND">AND (all must be true)</option>
                      <option value="OR">OR (any can be true)</option>
                    </select>
                  </div>
                )}
                {exitSignals.map((signal, idx) => (
                  <SignalBuilder
                    key={signal.id}
                    signal={signal}
                    onChange={(updates) => updateSignal(exitSignals, setExitSignals, signal.id, updates)}
                    onRemove={() => removeSignal(exitSignals, setExitSignals, signal.id)}
                    canRemove={exitSignals.length > 1}
                    index={idx}
                  />
                ))}
              </CardContent>
            </Card>

            {/* Regime Filter */}
            <Card>
              <CardHeader>
                <CardTitle>Regime Filter (Optional)</CardTitle>
                <CardDescription>Only trade in specific market conditions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {REGIMES.map((regime) => (
                    <label
                      key={regime}
                      className={`px-3 py-2 rounded-md border cursor-pointer transition-colors ${
                        regimeFilter.includes(regime)
                          ? "bg-blue-600 text-white border-blue-600"
                          : "bg-white dark:bg-neutral-900 border-neutral-300 dark:border-neutral-700 hover:border-blue-400"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={regimeFilter.includes(regime)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setRegimeFilter([...regimeFilter, regime]);
                          } else {
                            setRegimeFilter(regimeFilter.filter(r => r !== regime));
                          }
                        }}
                        className="sr-only"
                      />
                      {regime}
                    </label>
                  ))}
                </div>
                <p className="text-xs text-neutral-500 mt-2">
                  Leave empty to trade in all regimes
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Create Button */}
            <Card>
              <CardContent className="pt-6">
                <Button
                  onClick={handleCreate}
                  disabled={loading || !name.trim()}
                  className="w-full"
                  size="lg"
                >
                  {loading ? (
                    <>
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Create Strategy
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Preview */}
            {showPreview && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">JSON Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="text-xs bg-neutral-900 text-neutral-100 p-3 rounded-md overflow-auto max-h-96">
                    {JSON.stringify(
                      {
                        name: name || "(name)",
                        description: description || "(description)",
                        entry_logic: buildLogicTree(entrySignals, entryOperator),
                        exit_logic: buildLogicTree(exitSignals, exitOperator),
                        regime_filter: regimeFilter.length > 0 ? regimeFilter : undefined,
                      },
                      null,
                      2
                    )}
                  </pre>
                </CardContent>
              </Card>
            )}

            {/* Tips */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Strategy Tips</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-neutral-600 dark:text-neutral-400 space-y-2">
                <p><strong>RSI:</strong> Values below 30 = oversold, above 70 = overbought</p>
                <p><strong>MACD:</strong> Cross above signal = bullish, below = bearish</p>
                <p><strong>BB:</strong> Price at lower band = potential buy, upper = sell</p>
                <p><strong>Regime tips:</strong></p>
                <ul className="list-disc list-inside text-xs">
                  <li>TREND_UP/DOWN: Use MACD, MA crossovers</li>
                  <li>RANGE: Use RSI, Bollinger Bands</li>
                  <li>CHOPPY: Consider avoiding</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

function SignalBuilder({
  signal,
  onChange,
  onRemove,
  canRemove,
  index,
}: {
  signal: Signal;
  onChange: (updates: Partial<Signal>) => void;
  onRemove: () => void;
  canRemove: boolean;
  index: number;
}) {
  const indicatorConfig = INDICATORS[signal.indicator as keyof typeof INDICATORS];

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-neutral-500">Condition {index + 1}</span>
        {canRemove && (
          <Button variant="ghost" size="sm" onClick={onRemove}>
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        )}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {/* Indicator Selection */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-neutral-500">Indicator</label>
          <select
            value={signal.indicator}
            onChange={(e) => {
              const newIndicator = e.target.value as keyof typeof INDICATORS;
              const config = INDICATORS[newIndicator];
              onChange({
                indicator: newIndicator,
                parameters: { ...config.parameters },
                condition: { ...config.defaultCondition },
                indicator_component: config.outputs.length > 1 ? config.outputs[0] : undefined,
              });
            }}
            className="w-full rounded-md border border-neutral-300 px-2 py-1.5 text-sm dark:border-neutral-700 dark:bg-neutral-900"
          >
            {Object.entries(INDICATORS).map(([key, config]) => (
              <option key={key} value={key}>
                {config.name} - {config.description}
              </option>
            ))}
          </select>
        </div>

        {/* Component (for multi-output indicators) */}
        {indicatorConfig.outputs.length > 1 && (
          <div className="space-y-1">
            <label className="text-xs font-medium text-neutral-500">Component</label>
            <select
              value={signal.indicator_component || indicatorConfig.outputs[0]}
              onChange={(e) => onChange({ indicator_component: e.target.value })}
              className="w-full rounded-md border border-neutral-300 px-2 py-1.5 text-sm dark:border-neutral-700 dark:bg-neutral-900"
            >
              {indicatorConfig.outputs.map((output) => (
                <option key={output} value={output}>
                  {output}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Parameters */}
      <div className="grid gap-2 grid-cols-2 md:grid-cols-4">
        {Object.entries(signal.parameters).map(([key, value]) => (
          <div key={key} className="space-y-1">
            <label className="text-xs font-medium text-neutral-500">{key}</label>
            <input
              type="number"
              value={value}
              onChange={(e) =>
                onChange({
                  parameters: { ...signal.parameters, [key]: Number(e.target.value) },
                })
              }
              className="w-full rounded-md border border-neutral-300 px-2 py-1.5 text-sm dark:border-neutral-700 dark:bg-neutral-900"
            />
          </div>
        ))}
      </div>

      {/* Condition */}
      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-1">
          <label className="text-xs font-medium text-neutral-500">Condition</label>
          <select
            value={signal.condition.operator}
            onChange={(e) =>
              onChange({ condition: { ...signal.condition, operator: e.target.value } })
            }
            className="w-full rounded-md border border-neutral-300 px-2 py-1.5 text-sm dark:border-neutral-700 dark:bg-neutral-900"
          >
            {CONDITION_OPERATORS.map((op) => (
              <option key={op.value} value={op.value}>
                {op.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-neutral-500">Value</label>
          <input
            type={typeof signal.condition.value === "number" ? "number" : "text"}
            value={signal.condition.value}
            onChange={(e) => {
              const val = e.target.value;
              const numVal = Number(val);
              onChange({
                condition: {
                  ...signal.condition,
                  value: isNaN(numVal) ? val : numVal,
                },
              });
            }}
            className="w-full rounded-md border border-neutral-300 px-2 py-1.5 text-sm dark:border-neutral-700 dark:bg-neutral-900"
            placeholder="30, 70, signal, price..."
          />
        </div>
      </div>
    </div>
  );
}
