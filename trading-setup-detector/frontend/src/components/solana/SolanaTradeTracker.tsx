'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { api } from '@/lib/api';
import { SolanaTrade, SolanaWallet, SolanaTradeStats } from '@/types';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
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
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface ProcessedTrade {
  id: number;
  token: string;
  tokenAddress: string;
  side: 'long' | 'short';
  status: 'open' | 'closed';
  entryPrice: number;
  exitPrice?: number;
  size: number;
  pnl?: number;
  pnlPercent?: number;
  entryDate: string;
  exitDate?: string;
  buyTrade: SolanaTrade;
  sellTrades: SolanaTrade[];
}

// Calendar Component
const DAYS_OF_WEEK = ['D', 'L', 'M', 'M', 'J', 'V', 'S'];
const MONTHS = [
  'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
  'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
];

function SolanaCalendar({ trades }: { trades: ProcessedTrade[] }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setSelectedDay(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Group trades by exit date
  const tradesByDay = useMemo(() => {
    const result: Record<string, ProcessedTrade[]> = {};

    trades.forEach((trade) => {
      if (trade.status === 'closed' && trade.exitDate && trade.pnl !== undefined) {
        const exitDate = new Date(trade.exitDate);
        const dateKey = `${exitDate.getFullYear()}-${exitDate.getMonth()}-${exitDate.getDate()}`;
        if (!result[dateKey]) result[dateKey] = [];
        result[dateKey].push(trade);
      }
    });

    return result;
  }, [trades]);

  // Calculate profit by day
  const profitByDay = useMemo(() => {
    const result: Record<string, number> = {};

    Object.entries(tradesByDay).forEach(([dateKey, dayTrades]) => {
      result[dateKey] = dayTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
    });

    return result;
  }, [tradesByDay]);

  // Calculate monthly totals
  const monthlyStats = useMemo(() => {
    let totalProfit = 0;

    Object.entries(profitByDay).forEach(([dateKey, profit]) => {
      const [year, month] = dateKey.split('-').map(Number);
      if (year === currentYear && month === currentMonth) {
        totalProfit += profit;
      }
    });

    return { totalProfit };
  }, [profitByDay, currentMonth, currentYear]);

  // Get days in month
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();

  const prevMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth - 1, 1));
    setSelectedDay(null);
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth + 1, 1));
    setSelectedDay(null);
  };

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const days = [];

    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push({ day: null, profit: null, trades: [] as ProcessedTrade[] });
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dateKey = `${currentYear}-${currentMonth}-${day}`;
      const profit = profitByDay[dateKey] || null;
      const dayTrades = tradesByDay[dateKey] || [];
      days.push({ day, profit, trades: dayTrades });
    }

    return days;
  }, [currentYear, currentMonth, daysInMonth, firstDayOfMonth, profitByDay, tradesByDay]);

  const formatProfit = (profit: number) => {
    if (Math.abs(profit) >= 1000) {
      return `${profit > 0 ? '+' : ''}${(profit / 1000).toFixed(1)}k`;
    }
    return `${profit > 0 ? '+' : ''}${profit.toFixed(0)}`;
  };

  const today = new Date();
  const isToday = (day: number) =>
    day === today.getDate() &&
    currentMonth === today.getMonth() &&
    currentYear === today.getFullYear();

  const handleDayClick = (day: number | null, hasTrades: boolean) => {
    if (day && hasTrades) {
      setSelectedDay(selectedDay === day ? null : day);
    }
  };

  const selectedDayTrades = selectedDay
    ? calendarDays.find(d => d.day === selectedDay)?.trades || []
    : [];

  return (
    <Card className="bg-zinc-900/50 w-[280px]" ref={popoverRef}>
      <CardHeader className="py-2 px-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={prevMonth}>
              <ChevronLeft className="h-3 w-3" />
            </Button>
            <span className="text-xs font-medium text-white min-w-[80px] text-center">
              {MONTHS[currentMonth]} {currentYear}
            </span>
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={nextMonth}>
              <ChevronRight className="h-3 w-3" />
            </Button>
          </div>
          <span className={`text-xs ${monthlyStats.totalProfit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {monthlyStats.totalProfit >= 0 ? '+' : ''}${monthlyStats.totalProfit.toFixed(0)}
          </span>
        </div>
      </CardHeader>

      <CardContent className="px-2 pb-2 pt-0">
        <div className="grid grid-cols-7 gap-0.5 mb-0.5">
          {DAYS_OF_WEEK.map((day, i) => (
            <div key={i} className="text-center text-[9px] text-zinc-600 w-9">
              {day}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-0.5">
          {calendarDays.map((item, index) => (
            <div
              key={index}
              onClick={() => handleDayClick(item.day, item.trades.length > 0)}
              className={`
                h-9 w-9 rounded text-center flex flex-col items-center justify-center
                ${item.day === null ? 'bg-transparent' : 'bg-zinc-800/30'}
                ${item.profit !== null && item.profit > 0 ? 'bg-green-500/25' : ''}
                ${item.profit !== null && item.profit < 0 ? 'bg-red-500/25' : ''}
                ${isToday(item.day || 0) ? 'ring-1 ring-blue-500' : ''}
                ${selectedDay && selectedDay === item.day ? 'ring-2 ring-white' : ''}
                ${item.trades.length > 0 ? 'cursor-pointer hover:ring-1 hover:ring-zinc-500' : ''}
              `}
            >
              {item.day && (
                <>
                  <span className={`text-[9px] leading-none ${isToday(item.day) ? 'text-blue-400 font-bold' : 'text-zinc-500'}`}>
                    {item.day}
                  </span>
                  {item.profit !== null && (
                    <span className={`text-[9px] font-medium leading-none ${item.profit > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatProfit(item.profit)}
                    </span>
                  )}
                </>
              )}
            </div>
          ))}
        </div>

        {selectedDay && selectedDayTrades.length > 0 && (
          <div className="mt-2 pt-2 border-t border-zinc-800">
            <p className="text-[10px] text-zinc-500 mb-1.5">{selectedDay} de {MONTHS[currentMonth]}</p>
            <div className="space-y-1">
              {selectedDayTrades.map((trade) => (
                <div key={trade.id} className="flex items-center justify-between text-[11px] bg-zinc-800/50 rounded px-2 py-1">
                  <div className="flex items-center gap-1.5">
                    <TrendingUp className="h-3 w-3 text-green-400" />
                    <span className="text-white font-medium">{trade.token}</span>
                  </div>
                  <span className={trade.pnl && trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                    {trade.pnl && trade.pnl >= 0 ? '+' : ''}${trade.pnl?.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function SolanaTradeTracker() {
  const [wallets, setWallets] = useState<SolanaWallet[]>([]);
  const [trades, setTrades] = useState<SolanaTrade[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTrade, setExpandedTrade] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>('all');

  // Wallet form
  const [newWalletAddress, setNewWalletAddress] = useState('');
  const [newWalletLabel, setNewWalletLabel] = useState('');
  const [addingWallet, setAddingWallet] = useState(false);
  const [showWalletForm, setShowWalletForm] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [walletsData, tradesData] = await Promise.all([
        api.getSolanaWallets(),
        api.getSolanaTrades({})
      ]);
      setWallets(walletsData as SolanaWallet[]);
      setTrades((tradesData as { trades: SolanaTrade[] }).trades || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Process trades into unified view (group buys with their sells)
  const processedTrades: ProcessedTrade[] = useMemo(() => {
    const buys = trades.filter(t => t.side === 'buy');
    const sells = trades.filter(t => t.side === 'sell');

    return buys.map(buy => {
      const linkedSells = sells.filter(s => s.linked_trade_id === buy.id);
      const totalSold = linkedSells.reduce((sum, s) => sum + s.token_in_amount, 0);
      const totalPnl = linkedSells.reduce((sum, s) => sum + (s.pnl || 0), 0);
      const avgExitPrice = linkedSells.length > 0
        ? linkedSells.reduce((sum, s) => sum + (s.price_per_token || 0), 0) / linkedSells.length
        : undefined;

      const isClosed = totalSold >= buy.token_out_amount * 0.99;
      const entryUsd = buy.token_in_usd_value || 0;
      const pnlPercent = entryUsd > 0 ? (totalPnl / entryUsd) * 100 : 0;

      return {
        id: buy.id,
        token: buy.token_out_symbol || 'Unknown',
        tokenAddress: buy.token_out_address,
        side: 'long' as const,
        status: isClosed ? 'closed' as const : 'open' as const,
        entryPrice: buy.price_per_token || 0,
        exitPrice: avgExitPrice,
        size: buy.token_in_usd_value || 0,
        pnl: totalPnl || undefined,
        pnlPercent: totalPnl ? pnlPercent : undefined,
        entryDate: buy.block_time,
        exitDate: linkedSells.length > 0 ? linkedSells[linkedSells.length - 1].block_time : undefined,
        buyTrade: buy,
        sellTrades: linkedSells,
      };
    }).sort((a, b) => new Date(b.entryDate).getTime() - new Date(a.entryDate).getTime());
  }, [trades]);

  // Filter trades
  const filteredTrades = useMemo(() => {
    if (filter === 'all') return processedTrades;
    if (filter === 'open') return processedTrades.filter(t => t.status === 'open');
    if (filter === 'closed') return processedTrades.filter(t => t.status === 'closed');
    return processedTrades;
  }, [processedTrades, filter]);

  // Calculate stats from processed trades
  const calculatedStats = useMemo(() => {
    const closed = processedTrades.filter(t => t.status === 'closed');
    const winners = closed.filter(t => (t.pnl || 0) > 0);
    const losers = closed.filter(t => (t.pnl || 0) < 0);
    const totalPnl = closed.reduce((sum, t) => sum + (t.pnl || 0), 0);
    const avgPnl = closed.length > 0 ? totalPnl / closed.length : 0;
    const winRate = closed.length > 0 ? (winners.length / closed.length) * 100 : 0;
    const bestTrade = closed.length > 0 ? Math.max(...closed.map(t => t.pnl || 0)) : 0;
    const worstTrade = closed.length > 0 ? Math.min(...closed.map(t => t.pnl || 0)) : 0;

    return {
      totalTrades: closed.length,
      winners: winners.length,
      losers: losers.length,
      winRate,
      totalPnl,
      avgPnl,
      bestTrade,
      worstTrade,
    };
  }, [processedTrades]);

  const handleAddWallet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWalletAddress) return;

    try {
      setAddingWallet(true);
      await api.addSolanaWallet(newWalletAddress, newWalletLabel || undefined);
      setNewWalletAddress('');
      setNewWalletLabel('');
      setShowWalletForm(false);
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

  const formatNumber = (num: number | null | undefined, decimals = 2) => {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  };

  const formatPrice = (price: number) => {
    if (price >= 1) return price.toFixed(2);
    if (price >= 0.01) return price.toFixed(4);
    return price.toFixed(6);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const shortenAddress = (address: string) => {
    return `${address.slice(0, 4)}...${address.slice(-4)}`;
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-end gap-2">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg px-3 py-2 text-sm"
        >
          <option value="all">Todos</option>
          <option value="open">Abiertos</option>
          <option value="closed">Cerrados</option>
        </select>
        <Button variant="outline" size="sm" onClick={loadData}>
          <RefreshCw className="h-4 w-4" />
        </Button>
        <Button size="sm" onClick={() => setShowWalletForm(!showWalletForm)}>
          <Wallet className="mr-2 h-4 w-4" />
          Wallets ({wallets.length})
        </Button>
      </div>

      {/* Wallet Management */}
      {showWalletForm && (
        <Card className="border-purple-500/50">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Wallet className="h-5 w-5" />
                Wallets Monitoreadas
              </h3>
            </div>

            <form onSubmit={handleAddWallet} className="flex gap-2 mb-4">
              <Input
                placeholder="Dirección de wallet Solana"
                value={newWalletAddress}
                onChange={(e) => setNewWalletAddress(e.target.value)}
                className="flex-1 bg-zinc-800 border-zinc-700 text-white"
              />
              <Input
                placeholder="Label"
                value={newWalletLabel}
                onChange={(e) => setNewWalletLabel(e.target.value)}
                className="w-32 bg-zinc-800 border-zinc-700 text-white"
              />
              <Button type="submit" disabled={addingWallet || !newWalletAddress}>
                <Plus className="h-4 w-4" />
              </Button>
            </form>

            <div className="space-y-2">
              {wallets.map((wallet) => (
                <div
                  key={wallet.id}
                  className="flex items-center justify-between p-2 bg-zinc-800 rounded"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-white">
                      {shortenAddress(wallet.address)}
                    </span>
                    {wallet.label && (
                      <span className="text-xs text-zinc-400">({wallet.label})</span>
                    )}
                    {wallet.helius_webhook_id && (
                      <Badge variant="outline" className="text-emerald-400 border-emerald-400 text-xs">
                        Webhook
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
                <p className="text-center text-zinc-500 py-2 text-sm">
                  No hay wallets. Agrega una para trackear trades.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Row */}
      {calculatedStats.totalTrades > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500 mb-1">Total Trades</p>
              <p className="text-xl font-bold text-white">{calculatedStats.totalTrades}</p>
              <p className="text-xs text-zinc-400">
                <span className="text-green-400">{calculatedStats.winners}W</span>
                {' / '}
                <span className="text-red-400">{calculatedStats.losers}L</span>
              </p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500 mb-1">Win Rate</p>
              <p className={`text-xl font-bold ${calculatedStats.winRate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                {calculatedStats.winRate.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500 mb-1">Total PnL</p>
              <p className={`text-xl font-bold ${calculatedStats.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {calculatedStats.totalPnl >= 0 ? '+' : ''}${formatNumber(calculatedStats.totalPnl)}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500 mb-1">Avg PnL</p>
              <p className={`text-xl font-bold ${calculatedStats.avgPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {calculatedStats.avgPnl >= 0 ? '+' : ''}${formatNumber(calculatedStats.avgPnl)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content: Calendar + Trades */}
      <div className="flex gap-4">
        {/* Left Sidebar: Calendar + Summary */}
        <div className="hidden lg:flex flex-col gap-3 flex-shrink-0">
          <SolanaCalendar trades={processedTrades} />
          {calculatedStats.totalTrades > 0 && (
            <Card className="bg-zinc-900/50 w-[280px]">
              <CardContent className="p-3">
                <p className="text-xs text-zinc-500 mb-2">Resumen</p>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Mejor trade:</span>
                    <span className="text-green-400 font-medium">+${formatNumber(calculatedStats.bestTrade)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Peor trade:</span>
                    <span className="text-red-400 font-medium">${formatNumber(calculatedStats.worstTrade)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Trades List */}
        <div className="flex-1">
          {loading ? (
            <div className="py-8" />
          ) : filteredTrades.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-zinc-400">No hay trades. Los swaps aparecerán automáticamente.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {filteredTrades.map((trade) => (
                <Card
                  key={trade.id}
                  className={`border-l-4 ${
                    trade.status === 'open'
                      ? 'border-l-yellow-500'
                      : trade.pnl && trade.pnl > 0
                      ? 'border-l-green-500'
                      : 'border-l-red-500'
                  }`}
                >
                  <CardContent className="py-3">
                    <div
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setExpandedTrade(expandedTrade === trade.id ? null : trade.id)}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded ${trade.side === 'long' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                          {trade.side === 'long' ? (
                            <TrendingUp className="h-4 w-4 text-green-400" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-400" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white">{trade.token}</span>
                            <Badge variant="success" className="text-xs">
                              LONG
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {trade.status === 'open' ? 'Abierto' : 'Cerrado'}
                            </Badge>
                          </div>
                          <div className="text-xs text-zinc-400">
                            Entry: ${formatPrice(trade.entryPrice)} • Size: ${formatNumber(trade.size, 0)}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        {trade.status === 'closed' && trade.pnl !== undefined && (
                          <div className="text-right">
                            <div className={`font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {trade.pnl >= 0 ? '+' : ''}${formatNumber(trade.pnl)}
                            </div>
                            <div className={`text-xs ${trade.pnlPercent && trade.pnlPercent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {trade.pnlPercent && trade.pnlPercent >= 0 ? '+' : ''}{formatNumber(trade.pnlPercent)}%
                            </div>
                          </div>
                        )}
                        <div className="text-xs text-zinc-500">
                          {formatDate(trade.entryDate)}
                        </div>
                        {expandedTrade === trade.id ? (
                          <ChevronUp className="h-4 w-4 text-zinc-400" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-zinc-400" />
                        )}
                      </div>
                    </div>

                    {/* Expanded content */}
                    {expandedTrade === trade.id && (
                      <div className="mt-4 pt-4 border-t border-zinc-800 space-y-3">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-zinc-400">Entry:</span>
                            <span className="ml-2 text-white">${formatPrice(trade.entryPrice)}</span>
                          </div>
                          {trade.exitPrice && (
                            <div>
                              <span className="text-zinc-400">Exit:</span>
                              <span className="ml-2 text-white">${formatPrice(trade.exitPrice)}</span>
                            </div>
                          )}
                          <div>
                            <span className="text-zinc-400">Amount:</span>
                            <span className="ml-2 text-white">
                              {formatNumber(trade.buyTrade.token_out_amount, 4)} {trade.token}
                            </span>
                          </div>
                          <div>
                            <span className="text-zinc-400">Sells:</span>
                            <span className="ml-2 text-white">{trade.sellTrades.length}</span>
                          </div>
                        </div>

                        {/* Sell breakdown */}
                        {trade.sellTrades.length > 0 && (
                          <div className="space-y-1">
                            <p className="text-xs text-zinc-500">Ventas:</p>
                            {trade.sellTrades.map((sell, idx) => (
                              <div key={sell.id} className="text-xs text-zinc-400 flex justify-between">
                                <span>
                                  #{idx + 1}: {formatNumber(sell.token_in_amount, 4)} {trade.token} @ ${formatPrice(sell.price_per_token || 0)}
                                </span>
                                <span className={sell.pnl && sell.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                                  {sell.pnl && sell.pnl >= 0 ? '+' : ''}${formatNumber(sell.pnl)}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Links */}
                        <div className="flex gap-4 text-sm">
                          <a
                            href={`https://solscan.io/tx/${trade.buyTrade.tx_signature}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-purple-400 hover:text-purple-300 flex items-center gap-1"
                          >
                            <ExternalLink className="h-3 w-3" /> Entry TX
                          </a>
                          <a
                            href={`https://dexscreener.com/solana/${trade.tokenAddress}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-purple-400 hover:text-purple-300 flex items-center gap-1"
                          >
                            <ExternalLink className="h-3 w-3" /> DexScreener
                          </a>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
