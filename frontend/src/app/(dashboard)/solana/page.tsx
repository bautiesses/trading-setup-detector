'use client';

import { SolanaTradeTracker } from '@/components/solana/SolanaTradeTracker';

export default function SolanaPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Solana Trades</h1>
        <p className="text-zinc-400 mt-1">
          Tracking automatico de swaps en Jupiter via Helius webhooks
        </p>
      </div>

      <SolanaTradeTracker />
    </div>
  );
}
