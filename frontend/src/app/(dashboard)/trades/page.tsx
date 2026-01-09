'use client';

import { TradeTracker } from '@/components/trades/TradeTracker';

export default function TradesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Trade Tracker</h1>
        <p className="text-zinc-400 mt-1">Registra y trackea tus operaciones</p>
      </div>

      <TradeTracker />
    </div>
  );
}
