'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '@/lib/contexts/AuthContext';
import { useUsage, useUsageHistory } from '@/lib/hooks/useUsage';
import { apiEndpoint } from '@/lib/config';
import { CreditCard, User, BarChart3, RefreshCw } from 'lucide-react';

function BalanceColor({ balance }: { balance: number }) {
  if (balance > 2) return <span className="text-green-400">${balance.toFixed(2)}</span>;
  if (balance > 0.5) return <span className="text-yellow-400">${balance.toFixed(2)}</span>;
  return <span className="text-red-400">${balance.toFixed(2)}</span>;
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: 'bg-green-900/30 text-green-400 border-green-700',
    pending: 'bg-yellow-900/30 text-yellow-400 border-yellow-700',
    suspended: 'bg-red-900/30 text-red-400 border-red-700',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs border ${colors[status] || colors.pending}`}>
      {status}
    </span>
  );
}

const TOP_UP_AMOUNTS = [2, 5, 10];

function TopUpButtons({ onSuccess }: { onSuccess: () => void }) {
  const [loading, setLoading] = useState<number | null>(null);
  const [error, setError] = useState('');

  const handleTopUp = async (amount: number) => {
    setLoading(amount);
    setError('');

    try {
      const res = await fetch(apiEndpoint('/billing/create-checkout-session'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.detail || 'Failed to create checkout session');
        return;
      }

      const { checkout_url } = await res.json();
      if (checkout_url) {
        window.location.href = checkout_url;
      }
    } catch {
      setError('Something went wrong');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-3">
      <span className="text-neutral-400 text-sm">Top Up Credits</span>
      <div className="flex gap-2">
        {TOP_UP_AMOUNTS.map((amount) => (
          <button
            key={amount}
            onClick={() => handleTopUp(amount)}
            disabled={loading !== null}
            className="px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading === amount ? 'Redirecting...' : `$${amount}`}
          </button>
        ))}
      </div>
      {error && (
        <p className="text-red-400 text-sm">{error}</p>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const { usage, plan, loading, refresh } = useUsage();
  const { history, loading: historyLoading } = useUsageHistory(30);
  const [refreshing, setRefreshing] = useState(false);
  const [checkoutStatus, setCheckoutStatus] = useState<string | null>(null);

  // Handle Stripe redirect
  useEffect(() => {
    const status = searchParams.get('checkout');
    if (status === 'success') {
      setCheckoutStatus('success');
      refresh(); // refresh balance after successful payment
    } else if (status === 'cancelled') {
      setCheckoutStatus('cancelled');
    }
  }, [searchParams, refresh]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refresh();
    setRefreshing(false);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {checkoutStatus === 'success' && (
        <div className="p-3 rounded-lg bg-green-900/20 border border-green-700/50 text-green-400 text-sm flex items-center justify-between">
          <span>Payment successful! Your credits have been added.</span>
          <button onClick={() => setCheckoutStatus(null)} className="text-green-400 hover:text-green-300 ml-4">
            &times;
          </button>
        </div>
      )}
      {checkoutStatus === 'cancelled' && (
        <div className="p-3 rounded-lg bg-yellow-900/20 border border-yellow-700/50 text-yellow-400 text-sm flex items-center justify-between">
          <span>Payment was cancelled.</span>
          <button onClick={() => setCheckoutStatus(null)} className="text-yellow-400 hover:text-yellow-300 ml-4">
            &times;
          </button>
        </div>
      )}

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Account Section */}
      <section className="bg-neutral-800/50 border border-neutral-700 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <User className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold text-white">Account</h2>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-neutral-400">Email</span>
            <p className="text-white">{user?.email || '—'}</p>
          </div>
          <div>
            <span className="text-neutral-400">Name</span>
            <p className="text-white">{user?.name || '—'}</p>
          </div>
          <div>
            <span className="text-neutral-400">Status</span>
            <p className="mt-1">
              {plan ? <StatusBadge status={plan.account_status} /> : '—'}
            </p>
          </div>
        </div>
      </section>

      {/* Credits Section */}
      <section className="bg-neutral-800/50 border border-neutral-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <CreditCard className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg font-semibold text-white">Credits</h2>
          </div>
        </div>

        {loading ? (
          <div className="animate-pulse space-y-3">
            <div className="h-10 bg-neutral-700 rounded w-32" />
            <div className="h-4 bg-neutral-700 rounded w-48" />
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <span className="text-neutral-400 text-sm">Current Balance</span>
              <p className="text-3xl font-bold">
                <BalanceColor balance={plan?.credits_balance ?? 0} />
              </p>
            </div>

            {(plan?.credits_balance ?? 0) < 0.5 && (
              <div className="p-3 rounded-lg bg-yellow-900/20 border border-yellow-700/50 text-yellow-400 text-sm">
                Low balance — top up to continue using agent chat and other paid features.
              </div>
            )}

            <TopUpButtons onSuccess={handleRefresh} />
          </div>
        )}
      </section>

      {/* Usage This Month */}
      <section className="bg-neutral-800/50 border border-neutral-700 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold text-white">Usage This Month</h2>
        </div>

        {loading ? (
          <div className="animate-pulse space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-4 bg-neutral-700 rounded w-48" />
            ))}
          </div>
        ) : usage ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-neutral-900/50 rounded-lg p-3">
              <span className="text-neutral-400 text-xs">Agent Chats</span>
              <p className="text-xl font-bold text-white">{usage.agent_chat_count}</p>
            </div>
            <div className="bg-neutral-900/50 rounded-lg p-3">
              <span className="text-neutral-400 text-xs">Backtests</span>
              <p className="text-xl font-bold text-white">{usage.backtest_count}</p>
            </div>
            <div className="bg-neutral-900/50 rounded-lg p-3">
              <span className="text-neutral-400 text-xs">Data Fetches</span>
              <p className="text-xl font-bold text-white">{usage.data_fetch_count}</p>
            </div>
            <div className="bg-neutral-900/50 rounded-lg p-3">
              <span className="text-neutral-400 text-xs">Total Cost</span>
              <p className="text-xl font-bold text-white">${usage.total_cost_usd.toFixed(4)}</p>
            </div>
          </div>
        ) : (
          <p className="text-neutral-500 text-sm">No usage data available</p>
        )}
      </section>

      {/* Recent Activity */}
      <section className="bg-neutral-800/50 border border-neutral-700 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Recent Activity</h2>

        {historyLoading ? (
          <div className="animate-pulse space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-8 bg-neutral-700 rounded" />
            ))}
          </div>
        ) : history && (history.events.length > 0 || history.transactions.length > 0) ? (
          <div className="space-y-4">
            {/* Credit transactions */}
            {history.transactions.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-neutral-400 mb-2">Credit Transactions</h3>
                <div className="space-y-1">
                  {history.transactions.slice(0, 10).map((tx) => (
                    <div key={tx.id} className="flex items-center justify-between py-2 px-3 rounded bg-neutral-900/50 text-sm">
                      <div className="flex items-center gap-3">
                        <span className={tx.amount > 0 ? 'text-green-400' : 'text-red-400'}>
                          {tx.amount > 0 ? '+' : ''}{tx.amount.toFixed(4)}
                        </span>
                        <span className="text-neutral-400">{tx.description}</span>
                      </div>
                      <div className="flex items-center gap-3 text-neutral-500">
                        <span>bal: ${tx.balance_after.toFixed(2)}</span>
                        <span>{new Date(tx.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Usage events */}
            {history.events.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-neutral-400 mb-2">Usage Events</h3>
                <div className="space-y-1">
                  {history.events.slice(0, 10).map((ev) => (
                    <div key={ev.id} className="flex items-center justify-between py-2 px-3 rounded bg-neutral-900/50 text-sm">
                      <div className="flex items-center gap-3">
                        <span className="px-2 py-0.5 rounded bg-neutral-700 text-neutral-300 text-xs">
                          {ev.event_type}
                        </span>
                        {ev.cost_usd > 0 && (
                          <span className="text-neutral-400">${ev.cost_usd.toFixed(4)}</span>
                        )}
                        {ev.input_tokens > 0 && (
                          <span className="text-neutral-500">{ev.input_tokens.toLocaleString()} tokens</span>
                        )}
                      </div>
                      <span className="text-neutral-500">
                        {new Date(ev.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-neutral-500 text-sm">No activity yet</p>
        )}
      </section>
    </div>
  );
}
