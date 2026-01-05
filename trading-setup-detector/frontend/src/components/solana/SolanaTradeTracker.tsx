'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { SolanaTrade, SolanaWallet, SolanaTradeStats } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Wallet,
  Plus,
  Trash2,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Link as LinkIcon,
  RefreshCw,
  Image as ImageIcon
} from 'lucide-react';

export function SolanaTradeTracker() {
  const [wallets, setWallets] = useState<SolanaWallet[]>([]);
  const [trades, setTrades] = useState<SolanaTrade[]>([]);
  const [stats, setStats] = useState<SolanaTradeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'buy' | 'sell'>('all');

  // Wallet form
  const [newWalletAddress, setNewWalletAddress] = useState('');
  const [newWalletLabel, setNewWalletLabel] = useState('');
  const [addingWallet, setAddingWallet] = useState(false);

  // Link trades
  const [linkMode, setLinkMode] = useState(false);
  const [selectedEntryTrade, setSelectedEntryTrade] = useState<number | null>(null);


  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [walletsData, tradesData, statsData] = await Promise.all([
        api.getSolanaWallets(),
        api.getSolanaTrades({ side: filter === 'all' ? undefined : filter }),
        api.getSolanaStats()
      ]);
      setWallets(walletsData as SolanaWallet[]);
      setTrades((tradesData as { trades: SolanaTrade[] }).trades || []);
      setStats(statsData as SolanaTradeStats);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddWallet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWalletAddress) return;

    try {
      setAddingWallet(true);
      await api.addSolanaWallet(newWalletAddress, newWalletLabel || undefined);
      setNewWalletAddress('');
      setNewWalletLabel('');
      await loadData();
    } catch (error) {
      console.error('Error adding wallet:', error);
      alert('Error agregando wallet');
    } finally {
      setAddingWallet(false);
    }
  };

  const handleRemoveWallet = async (walletId: number) => {
    if (!confirm('Eliminar esta wallet?')) return;

    try {
      await api.removeSolanaWallet(walletId);
      await loadData();
    } catch (error) {
      console.error('Error removing wallet:', error);
    }
  };

  const handleLinkTrades = async (exitTradeId: number) => {
    if (!selectedEntryTrade) return;

    try {
      await api.linkSolanaTrades(selectedEntryTrade, exitTradeId);
      setLinkMode(false);
      setSelectedEntryTrade(null);
      await loadData();
    } catch (error) {
      console.error('Error linking trades:', error);
      alert('Error vinculando trades. El entry debe ser BUY y el exit debe ser SELL.');
    }
  };

  const formatNumber = (num: number | null, decimals = 2) => {
    if (num === null) return '-';
    return num.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const shortenAddress = (address: string) => {
    return `${address.slice(0, 4)}...${address.slice(-4)}`;
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-white">{stats.total_trades}</div>
              <p className="text-sm text-zinc-400">Total Trades</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-emerald-500">{stats.buy_trades}</div>
              <p className="text-sm text-zinc-400">Buys</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-red-500">{stats.sell_trades}</div>
              <p className="text-sm text-zinc-400">Sells</p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900 border-zinc-800">
            <CardContent className="pt-6">
              <div className={`text-2xl font-bold ${stats.linked_pnl >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                ${formatNumber(stats.linked_pnl)}
              </div>
              <p className="text-sm text-zinc-400">PnL (linked)</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Wallets */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Wallet className="h-5 w-5" />
            Wallets Monitoreadas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Add wallet form */}
          <form onSubmit={handleAddWallet} className="flex gap-2">
            <Input
              placeholder="Dirección de wallet Solana"
              value={newWalletAddress}
              onChange={(e) => setNewWalletAddress(e.target.value)}
              className="flex-1 bg-zinc-800 border-zinc-700 text-white"
            />
            <Input
              placeholder="Label (opcional)"
              value={newWalletLabel}
              onChange={(e) => setNewWalletLabel(e.target.value)}
              className="w-40 bg-zinc-800 border-zinc-700 text-white"
            />
            <Button type="submit" disabled={addingWallet || !newWalletAddress}>
              <Plus className="h-4 w-4 mr-1" />
              Agregar
            </Button>
          </form>

          {/* Wallet list */}
          <div className="space-y-2">
            {wallets.map((wallet) => (
              <div
                key={wallet.id}
                className="flex items-center justify-between p-3 bg-zinc-800 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <Wallet className="h-4 w-4 text-purple-400" />
                  <div>
                    <div className="font-mono text-sm text-white">
                      {shortenAddress(wallet.address)}
                    </div>
                    {wallet.label && (
                      <div className="text-xs text-zinc-400">{wallet.label}</div>
                    )}
                  </div>
                  {wallet.helius_webhook_id && (
                    <Badge variant="outline" className="text-emerald-400 border-emerald-400">
                      Webhook activo
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <a
                    href={`https://solscan.io/account/${wallet.address}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                  <button
                    onClick={() => handleRemoveWallet(wallet.id)}
                    className="text-zinc-400 hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
            {wallets.length === 0 && (
              <p className="text-center text-zinc-500 py-4">
                No hay wallets. Agrega una para empezar a trackear tus trades de Jupiter.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Trades */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-white">Jupiter Trades</CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant={linkMode ? "destructive" : "outline"}
                size="sm"
                onClick={() => {
                  setLinkMode(!linkMode);
                  setSelectedEntryTrade(null);
                }}
              >
                <LinkIcon className="h-4 w-4 mr-1" />
                {linkMode ? 'Cancelar Link' : 'Link Trades'}
              </Button>
              <Button variant="outline" size="sm" onClick={loadData}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
          {/* Filters */}
          <div className="flex gap-2 mt-4">
            {(['all', 'buy', 'sell'] as const).map((f) => (
              <Button
                key={f}
                variant={filter === f ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter(f)}
              >
                {f === 'all' ? 'Todos' : f === 'buy' ? 'Buys' : 'Sells'}
              </Button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {linkMode && (
            <div className="mb-4 p-3 bg-purple-900/30 border border-purple-500 rounded-lg">
              <p className="text-sm text-purple-200">
                {selectedEntryTrade
                  ? 'Ahora selecciona el trade SELL para vincular'
                  : 'Selecciona primero un trade BUY (entry)'}
              </p>
            </div>
          )}

          <div className="space-y-3">
            {loading ? (
              <p className="text-center text-zinc-500 py-8">Cargando...</p>
            ) : trades.length === 0 ? (
              <p className="text-center text-zinc-500 py-8">
                No hay trades. Los swaps de Jupiter aparecerán aquí automáticamente.
              </p>
            ) : (
              trades.map((trade) => (
                <div
                  key={trade.id}
                  className={`p-4 rounded-lg border ${
                    linkMode && selectedEntryTrade === trade.id
                      ? 'border-purple-500 bg-purple-900/20'
                      : 'border-zinc-800 bg-zinc-800/50'
                  } ${
                    linkMode ? 'cursor-pointer hover:border-purple-400' : ''
                  }`}
                  onClick={() => {
                    if (!linkMode) return;
                    if (!selectedEntryTrade && trade.side === 'buy') {
                      setSelectedEntryTrade(trade.id);
                    } else if (selectedEntryTrade && trade.side === 'sell') {
                      handleLinkTrades(trade.id);
                    }
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      {trade.side === 'buy' ? (
                        <TrendingUp className="h-5 w-5 text-emerald-500" />
                      ) : (
                        <TrendingDown className="h-5 w-5 text-red-500" />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="outline"
                            className={trade.side === 'buy' ? 'text-emerald-400 border-emerald-400' : 'text-red-400 border-red-400'}
                          >
                            {trade.side.toUpperCase()}
                          </Badge>
                          <span className="text-white font-medium">
                            {trade.token_out_symbol || shortenAddress(trade.token_out_address)}
                          </span>
                          {trade.linked_trade_id && (
                            <Badge variant="outline" className="text-purple-400 border-purple-400">
                              Linked
                            </Badge>
                          )}
                        </div>
                        <div className="text-sm text-zinc-400 mt-1">
                          {formatNumber(trade.token_in_amount, 4)} {trade.token_in_symbol || '???'} →{' '}
                          {formatNumber(trade.token_out_amount, 4)} {trade.token_out_symbol || '???'}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-zinc-300">
                        ${formatNumber(trade.token_in_usd_value || trade.token_out_usd_value)}
                      </div>
                      {trade.pnl !== null && (
                        <div className={`text-sm font-medium ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {trade.pnl >= 0 ? '+' : ''}${formatNumber(trade.pnl)} ({formatNumber(trade.pnl_percent)}%)
                        </div>
                      )}
                      <div className="text-xs text-zinc-500 mt-1">
                        {formatDate(trade.block_time)}
                      </div>
                    </div>
                  </div>

                  {/* Additional info */}
                  <div className="mt-3 pt-3 border-t border-zinc-700 flex items-center justify-between text-xs text-zinc-500">
                    <div className="flex items-center gap-4">
                      <span>Fee: {formatNumber(trade.fee_sol, 6)} SOL</span>
                      <a
                        href={`https://solscan.io/tx/${trade.tx_signature}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-purple-400 hover:text-purple-300 flex items-center gap-1"
                        onClick={(e) => e.stopPropagation()}
                      >
                        TX <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                    <a
                      href={`https://dexscreener.com/solana/${trade.side === 'buy' ? trade.token_out_address : trade.token_in_address}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-purple-400 hover:text-purple-300 flex items-center gap-1"
                    >
                      <ImageIcon className="h-3 w-3" /> DexScreener
                    </a>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

    </div>
  );
}
