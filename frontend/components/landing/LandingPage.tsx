'use client';

import Link from 'next/link';
import { signIn } from 'next-auth/react';
import { Beaker, Brain, TrendingUp, BarChart3, Shield } from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'AI Research Agent',
    description: 'Chat with Claude to design, validate, and iterate on trading strategies using natural language.',
    color: 'bg-blue-600',
  },
  {
    icon: TrendingUp,
    title: 'Strategy Backtesting',
    description: 'Test strategies on historical data with detailed metrics: Sharpe ratio, max drawdown, win rate.',
    color: 'bg-green-600',
  },
  {
    icon: BarChart3,
    title: 'Market Regime Detection',
    description: 'Automatically classify market conditions (trending, ranging, choppy) to pick the right strategy.',
    color: 'bg-purple-600',
  },
  {
    icon: Shield,
    title: 'Multi-Asset Support',
    description: 'Fetch and analyze data for any Binance trading pair across multiple timeframes.',
    color: 'bg-orange-600',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-neutral-900">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <Beaker className="w-7 h-7 text-purple-400" />
          <span className="text-lg font-bold text-white">Research Lab</span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="px-4 py-2 text-sm text-neutral-300 hover:text-white transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="px-4 py-2 text-sm rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 pt-20 pb-16 max-w-4xl mx-auto text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-white leading-tight">
          AI-Powered Trading
          <br />
          <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            Strategy Research
          </span>
        </h1>
        <p className="mt-6 text-lg text-neutral-400 max-w-2xl mx-auto">
          Design, backtest, and validate crypto trading strategies with an AI research agent.
          Go from idea to validated strategy in minutes, not days.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <button
            onClick={() => signIn('google', { callbackUrl: '/' })}
            className="flex items-center gap-3 px-6 py-3 rounded-lg bg-white text-neutral-900 font-medium hover:bg-neutral-100 transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            Continue with Google
          </button>
          <Link
            href="/register"
            className="px-6 py-3 rounded-lg border border-neutral-700 text-white font-medium hover:bg-neutral-800 transition-colors"
          >
            Sign up with Email
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-16 max-w-5xl mx-auto">
        <div className="grid gap-6 md:grid-cols-2">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="p-6 rounded-xl bg-neutral-800/50 border border-neutral-700"
            >
              <div className={`inline-flex p-3 rounded-lg ${feature.color} mb-4`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-neutral-400 text-sm leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-neutral-800 text-center">
        <p className="text-sm text-neutral-500">
          Research Lab &mdash; AI-powered backtesting platform
        </p>
      </footer>
    </div>
  );
}
