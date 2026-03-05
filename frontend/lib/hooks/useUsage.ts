'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiEndpoint } from '@/lib/config';

interface UsageSummary {
  total_cost_usd: number;
  total_events: number;
  total_input_tokens: number;
  total_output_tokens: number;
  agent_chat_count: number;
  backtest_count: number;
  data_fetch_count: number;
}

interface PlanInfo {
  credits_balance: number;
  account_status: string;
}

interface UsageEvent {
  id: string;
  event_type: string;
  endpoint: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

interface CreditTransaction {
  id: string;
  amount: number;
  type: string;
  balance_after: number;
  description: string;
  created_at: string;
}

interface UsageHistory {
  events: UsageEvent[];
  transactions: CreditTransaction[];
}

export function useUsage() {
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const [usageRes, planRes] = await Promise.all([
        fetch(apiEndpoint('/usage/me')),
        fetch(apiEndpoint('/user/plan')),
      ]);

      if (usageRes.ok) setUsage(await usageRes.json());
      if (planRes.ok) setPlan(await planRes.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load usage data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { usage, plan, loading, error, refresh };
}

export function useUsageHistory(limit = 50) {
  const [history, setHistory] = useState<UsageHistory | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(apiEndpoint(`/usage/history?limit=${limit}`))
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setHistory(data))
      .finally(() => setLoading(false));
  }, [limit]);

  return { history, loading };
}
