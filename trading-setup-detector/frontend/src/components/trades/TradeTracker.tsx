'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ImageEditor } from '@/components/image-editor';
import { TradeCalendar } from './TradeCalendar';
import { api } from '@/lib/api';
import {
  Plus,
  TrendingUp,
  TrendingDown,
  X,
  Check,
  Trash2,
  ImageIcon,
  DollarSign,
  Percent,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Pencil,
  PenTool,
} from 'lucide-react';

interface Trade {
  id: number;
  symbol: string;
  side: string;
  status: string;
  entry_price: number;
  exit_price: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  size: number;
  pnl: number | null;
  pnl_percent: number | null;
  fees: number;
  notes: string | null;
  image_url: string | null;
  exit_notes: string | null;
  exit_image_url: string | null;
  timeframe: string | null;
  strategy: string | null;
  entry_date: string;
  exit_date: string | null;
}

interface TradeStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  average_pnl: number;
  best_trade: number;
  worst_trade: number;
}

export function TradeTracker() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [stats, setStats] = useState<TradeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showCloseForm, setShowCloseForm] = useState<number | null>(null);
  const [editingTrade, setEditingTrade] = useState<Trade | null>(null);
  const [expandedTrade, setExpandedTrade] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [expandedImage, setExpandedImage] = useState<{
    url: string;
    type: 'entry' | 'exit';
    tradeId: number;
  } | null>(null);
  const [editingImage, setEditingImage] = useState<{
    source: 'entry' | 'exit' | 'closeForm' | 'viewEntry' | 'viewExit';
    imageUrl: string;
    tradeId?: number;
  } | null>(null);

  // Helper to get today's date in local format for input
  const getTodayDate = () => {
    const now = new Date();
    return now.toISOString().slice(0, 16); // Format: YYYY-MM-DDTHH:mm
  };

  // Form state
  const [formData, setFormData] = useState({
    symbol: '',
    side: 'long',
    entry_price: '',
    size: '',
    stop_loss: '',
    take_profit: '',
    notes: '',
    image_url: '',
    timeframe: '1h',
    strategy: 'Break & Retest',
    entry_date: getTodayDate(),
    // Exit fields (for editing closed trades)
    exit_price: '',
    exit_notes: '',
    exit_image_url: '',
    fees: '',
  });

  const [closeData, setCloseData] = useState({
    exit_price: '',
    fees: '',
    exit_notes: '',
    exit_image_url: '',
  });

  const closeFileInputRef = useRef<HTMLInputElement>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchTrades();
    fetchStats();
  }, [filter]);

  const fetchTrades = async () => {
    try {
      const status = filter === 'all' ? undefined : filter;
      const response = await api.getTrades(status) as { trades: Trade[]; total: number };
      setTrades(response.trades || []);
    } catch (error) {
      console.error('Error fetching trades:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await api.getTradeStats() as TradeStats;
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      symbol: '',
      side: 'long',
      entry_price: '',
      size: '',
      stop_loss: '',
      take_profit: '',
      notes: '',
      image_url: '',
      timeframe: '1h',
      strategy: 'Break & Retest',
      entry_date: getTodayDate(),
      exit_price: '',
      exit_notes: '',
      exit_image_url: '',
      fees: '',
    });
    setEditingTrade(null);
    setShowForm(false);
  };

  const handleEdit = (trade: Trade) => {
    setFormData({
      symbol: trade.symbol,
      side: trade.side,
      entry_price: trade.entry_price.toString(),
      size: trade.size.toString(),
      stop_loss: trade.stop_loss?.toString() || '',
      take_profit: trade.take_profit?.toString() || '',
      notes: trade.notes || '',
      image_url: trade.image_url || '',
      timeframe: trade.timeframe || '1h',
      strategy: trade.strategy || 'Break & Retest',
      entry_date: trade.entry_date ? new Date(trade.entry_date).toISOString().slice(0, 16) : getTodayDate(),
      // Exit fields
      exit_price: trade.exit_price?.toString() || '',
      exit_notes: trade.exit_notes || '',
      exit_image_url: trade.exit_image_url || '',
      fees: trade.fees?.toString() || '',
    });
    setEditingTrade(trade);
    setShowForm(true);
    setExpandedTrade(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const baseTradeData = {
        symbol: formData.symbol.toUpperCase(),
        side: formData.side,
        entry_price: parseFloat(formData.entry_price),
        size: parseFloat(formData.size),
        stop_loss: formData.stop_loss ? parseFloat(formData.stop_loss) : undefined,
        take_profit: formData.take_profit ? parseFloat(formData.take_profit) : undefined,
        notes: formData.notes || undefined,
        image_url: formData.image_url || undefined,
        timeframe: formData.timeframe || undefined,
        strategy: formData.strategy || undefined,
        entry_date: formData.entry_date ? new Date(formData.entry_date).toISOString() : undefined,
      };

      if (editingTrade) {
        // Include exit fields when editing a closed trade
        const updateData = editingTrade.status === 'closed' ? {
          ...baseTradeData,
          exit_price: formData.exit_price ? parseFloat(formData.exit_price) : undefined,
          exit_notes: formData.exit_notes || undefined,
          exit_image_url: formData.exit_image_url || undefined,
          fees: formData.fees ? parseFloat(formData.fees) : undefined,
        } : baseTradeData;
        await api.updateTrade(editingTrade.id, updateData);
      } else {
        await api.createTrade(baseTradeData);
      }

      resetForm();
      fetchTrades();
      fetchStats();
    } catch (error) {
      console.error('Error saving trade:', error);
    }
  };

  const handleClose = async (tradeId: number) => {
    try {
      await api.closeTrade(tradeId, {
        exit_price: parseFloat(closeData.exit_price),
        fees: closeData.fees ? parseFloat(closeData.fees) : 0,
        exit_notes: closeData.exit_notes || undefined,
        exit_image_url: closeData.exit_image_url || undefined,
      });
      setShowCloseForm(null);
      setCloseData({ exit_price: '', fees: '', exit_notes: '', exit_image_url: '' });
      fetchTrades();
      fetchStats();
    } catch (error) {
      console.error('Error closing trade:', error);
    }
  };

  const handleCloseImagePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) {
          const reader = new FileReader();
          reader.onload = (event) => {
            const base64 = event.target?.result as string;
            setCloseData({ ...closeData, exit_image_url: base64 });
          };
          reader.readAsDataURL(file);
        }
        break;
      }
    }
  };

  const handleCloseImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const base64 = event.target?.result as string;
        setCloseData({ ...closeData, exit_image_url: base64 });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDelete = async (tradeId: number) => {
    if (!confirm('¿Eliminar este trade?')) return;
    try {
      await api.deleteTrade(tradeId);
      fetchTrades();
      fetchStats();
    } catch (error) {
      console.error('Error deleting trade:', error);
    }
  };

  const handleImageEditorSave = async (editedBase64: string) => {
    if (!editingImage) return;

    if (editingImage.source === 'entry') {
      setFormData({ ...formData, image_url: editedBase64 });
    } else if (editingImage.source === 'exit') {
      setFormData({ ...formData, exit_image_url: editedBase64 });
    } else if (editingImage.source === 'closeForm') {
      setCloseData({ ...closeData, exit_image_url: editedBase64 });
    } else if (editingImage.source === 'viewEntry' && editingImage.tradeId) {
      // Update trade directly
      try {
        await api.updateTrade(editingImage.tradeId, { image_url: editedBase64 });
        fetchTrades();
      } catch (error) {
        console.error('Error updating trade image:', error);
      }
    } else if (editingImage.source === 'viewExit' && editingImage.tradeId) {
      try {
        await api.updateTrade(editingImage.tradeId, { exit_image_url: editedBase64 });
        fetchTrades();
      } catch (error) {
        console.error('Error updating trade exit image:', error);
      }
    }

    setEditingImage(null);
    setExpandedImage(null);
  };

  const handleImagePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) {
          const reader = new FileReader();
          reader.onload = (event) => {
            const base64 = event.target?.result as string;
            setFormData({ ...formData, image_url: base64 });
          };
          reader.readAsDataURL(file);
        }
        break;
      }
    }
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const base64 = event.target?.result as string;
        setFormData({ ...formData, image_url: base64 });
      };
      reader.readAsDataURL(file);
    }
  };

  const exitImageInputRef = useRef<HTMLInputElement>(null);

  const handleExitImagePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) {
          const reader = new FileReader();
          reader.onload = (event) => {
            const base64 = event.target?.result as string;
            setFormData({ ...formData, exit_image_url: base64 });
          };
          reader.readAsDataURL(file);
        }
        break;
      }
    }
  };

  const handleExitImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const base64 = event.target?.result as string;
        setFormData({ ...formData, exit_image_url: base64 });
      };
      reader.readAsDataURL(file);
    }
  };

  // Image navigation
  const getTradeById = (id: number) => trades.find(t => t.id === id);

  const navigateImage = (direction: 'prev' | 'next') => {
    if (!expandedImage) return;

    const trade = getTradeById(expandedImage.tradeId);
    if (!trade) return;

    if (direction === 'next' && expandedImage.type === 'entry' && trade.exit_image_url) {
      setExpandedImage({ url: trade.exit_image_url, type: 'exit', tradeId: trade.id });
    } else if (direction === 'prev' && expandedImage.type === 'exit' && trade.image_url) {
      setExpandedImage({ url: trade.image_url, type: 'entry', tradeId: trade.id });
    }
  };

  const canNavigate = (direction: 'prev' | 'next') => {
    if (!expandedImage) return false;
    const trade = getTradeById(expandedImage.tradeId);
    if (!trade) return false;

    if (direction === 'next') {
      return expandedImage.type === 'entry' && !!trade.exit_image_url;
    } else {
      return expandedImage.type === 'exit' && !!trade.image_url;
    }
  };

  // Keyboard navigation for image modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!expandedImage) return;

      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        navigateImage('next');
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        navigateImage('prev');
      } else if (e.key === 'Escape') {
        setExpandedImage(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [expandedImage, trades]);

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
      minute: '2-digit',
    });
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
        <Button onClick={() => {
          if (showForm && !editingTrade) {
            resetForm();
          } else {
            resetForm();
            setShowForm(true);
          }
        }} size="sm">
          <Plus className="mr-2 h-4 w-4" />
          Nuevo Trade
        </Button>
      </div>

      {/* Stats Row - 4 columns */}
      {stats && stats.total_trades > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Card className="bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500 mb-1">Total Trades</p>
              <p className="text-xl font-bold text-white">{stats.total_trades}</p>
              <p className="text-xs text-zinc-400">
                <span className="text-green-400">{stats.winning_trades}W</span>
                {' / '}
                <span className="text-red-400">{stats.losing_trades}L</span>
              </p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500 mb-1">Win Rate</p>
              <p className={`text-xl font-bold ${stats.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                {stats.win_rate.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500 mb-1">Total PnL</p>
              <p className={`text-xl font-bold ${stats.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {stats.total_pnl >= 0 ? '+' : ''}${stats.total_pnl.toFixed(2)}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-xs text-zinc-500 mb-1">Avg PnL</p>
              <p className={`text-xl font-bold ${stats.average_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {stats.average_pnl >= 0 ? '+' : ''}${stats.average_pnl.toFixed(2)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* New/Edit Trade Form */}
      {showForm && (
        <Card className={editingTrade ? "border-yellow-500/50" : "border-emerald-500/50"}>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">
                {editingTrade ? 'Editar Trade' : 'Nuevo Trade'}
              </h3>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div>
                  <label className="text-xs text-zinc-400">Símbolo</label>
                  <Input
                    value={formData.symbol}
                    onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                    placeholder="BTCUSDT"
                    required
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Lado</label>
                  <select
                    value={formData.side}
                    onChange={(e) => setFormData({ ...formData, side: e.target.value })}
                    className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="long">Long</option>
                    <option value="short">Short</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Entry Price</label>
                  <Input
                    type="number"
                    step="any"
                    value={formData.entry_price}
                    onChange={(e) => setFormData({ ...formData, entry_price: e.target.value })}
                    placeholder="50000"
                    required
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Size (USD)</label>
                  <Input
                    type="number"
                    step="any"
                    value={formData.size}
                    onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                    placeholder="100"
                    required
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Fecha</label>
                  <Input
                    type="datetime-local"
                    value={formData.entry_date}
                    onChange={(e) => setFormData({ ...formData, entry_date: e.target.value })}
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div>
                  <label className="text-xs text-zinc-400">Stop Loss</label>
                  <Input
                    type="number"
                    step="any"
                    value={formData.stop_loss}
                    onChange={(e) => setFormData({ ...formData, stop_loss: e.target.value })}
                    placeholder="49000"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Take Profit</label>
                  <Input
                    type="number"
                    step="any"
                    value={formData.take_profit}
                    onChange={(e) => setFormData({ ...formData, take_profit: e.target.value })}
                    placeholder="52000"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Timeframe</label>
                  <select
                    value={formData.timeframe}
                    onChange={(e) => setFormData({ ...formData, timeframe: e.target.value })}
                    className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="15m">15m</option>
                    <option value="1h">1h</option>
                    <option value="4h">4h</option>
                    <option value="1d">1d</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-zinc-400">Estrategia</label>
                  <Input
                    value={formData.strategy}
                    onChange={(e) => setFormData({ ...formData, strategy: e.target.value })}
                    placeholder="Break & Retest"
                    className="bg-zinc-800 border-zinc-700"
                  />
                </div>
              </div>

              {/* Image upload */}
              <div
                className="border-2 border-dashed border-zinc-700 rounded-lg p-4 text-center cursor-pointer hover:border-zinc-500 transition-colors"
                onPaste={handleImagePaste}
                onClick={() => !formData.image_url && fileInputRef.current?.click()}
              >
                {formData.image_url ? (
                  <div className="relative">
                    <img
                      src={formData.image_url}
                      alt="Trade screenshot"
                      className="max-h-48 mx-auto rounded"
                    />
                    <div className="absolute top-2 right-2 flex gap-1">
                      <Button
                        type="button"
                        variant="secondary"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingImage({ source: 'entry', imageUrl: formData.image_url });
                        }}
                        title="Editar imagen"
                      >
                        <PenTool className="h-4 w-4" />
                      </Button>
                      <Button
                        type="button"
                        variant="destructive"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          setFormData({ ...formData, image_url: '' });
                        }}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-zinc-400">
                    <ImageIcon className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">Pegar imagen (Ctrl+V) o click para subir</p>
                  </div>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </div>

              {/* Notes */}
              <div>
                <label className="text-xs text-zinc-400">Notas de entrada</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Análisis, razón del trade..."
                  className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-md px-3 py-2 text-sm min-h-[80px]"
                />
              </div>

              {/* Exit section - only show when editing a closed trade */}
              {editingTrade && editingTrade.status === 'closed' && (
                <div className="border-t border-zinc-700 pt-4 mt-4 space-y-4">
                  <h4 className="text-md font-semibold text-white">📉 Datos del Cierre</h4>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs text-zinc-400">Exit Price</label>
                      <Input
                        type="number"
                        step="any"
                        value={formData.exit_price}
                        onChange={(e) => setFormData({ ...formData, exit_price: e.target.value })}
                        placeholder="51000"
                        className="bg-zinc-800 border-zinc-700"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-zinc-400">Fees</label>
                      <Input
                        type="number"
                        step="any"
                        value={formData.fees}
                        onChange={(e) => setFormData({ ...formData, fees: e.target.value })}
                        placeholder="0"
                        className="bg-zinc-800 border-zinc-700"
                      />
                    </div>
                  </div>

                  {/* Exit Image upload */}
                  <div
                    className="border-2 border-dashed border-zinc-700 rounded-lg p-4 text-center cursor-pointer hover:border-zinc-500 transition-colors"
                    onPaste={handleExitImagePaste}
                    onClick={() => !formData.exit_image_url && exitImageInputRef.current?.click()}
                  >
                    {formData.exit_image_url ? (
                      <div className="relative">
                        <img
                          src={formData.exit_image_url}
                          alt="Exit screenshot"
                          className="max-h-48 mx-auto rounded"
                        />
                        <div className="absolute top-2 right-2 flex gap-1">
                          <Button
                            type="button"
                            variant="secondary"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingImage({ source: 'exit', imageUrl: formData.exit_image_url });
                            }}
                            title="Editar imagen"
                          >
                            <PenTool className="h-4 w-4" />
                          </Button>
                          <Button
                            type="button"
                            variant="destructive"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              setFormData({ ...formData, exit_image_url: '' });
                            }}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-zinc-400">
                        <ImageIcon className="h-8 w-8 mx-auto mb-2" />
                        <p className="text-sm">Pegar imagen de cierre (Ctrl+V) o click para subir</p>
                      </div>
                    )}
                    <input
                      ref={exitImageInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleExitImageUpload}
                      className="hidden"
                    />
                  </div>

                  {/* Exit Notes */}
                  <div>
                    <label className="text-xs text-zinc-400">Notas de cierre</label>
                    <textarea
                      value={formData.exit_notes}
                      onChange={(e) => setFormData({ ...formData, exit_notes: e.target.value })}
                      placeholder="Razón del cierre, lecciones aprendidas..."
                      className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-md px-3 py-2 text-sm min-h-[80px]"
                    />
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={resetForm}>
                  Cancelar
                </Button>
                <Button type="submit">
                  <Check className="mr-2 h-4 w-4" />
                  {editingTrade ? 'Guardar Cambios' : 'Guardar Trade'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Main Content: Calendar + Trades */}
      <div className="flex gap-4">
        {/* Left Sidebar: Calendar + Monthly Summary */}
        <div className="hidden lg:flex flex-col gap-3 flex-shrink-0">
          <TradeCalendar trades={trades} />
          {stats && stats.total_trades > 0 && (
            <Card className="bg-zinc-900/50 w-[280px]">
              <CardContent className="p-3">
                <p className="text-xs text-zinc-500 mb-2">Resumen</p>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Mejor trade:</span>
                    <span className="text-green-400 font-medium">+${stats.best_trade.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">Peor trade:</span>
                    <span className="text-red-400 font-medium">${stats.worst_trade.toFixed(2)}</span>
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
          ) : trades.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-zinc-400">No hay trades registrados.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {trades.map((trade) => (
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
                        <span className="font-bold text-white">{trade.symbol}</span>
                        <Badge variant={trade.side === 'long' ? 'success' : 'destructive'} className="text-xs">
                          {trade.side.toUpperCase()}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {trade.status === 'open' ? 'Abierto' : 'Cerrado'}
                        </Badge>
                      </div>
                      <div className="text-xs text-zinc-400">
                        Entry: ${formatPrice(trade.entry_price)} • Size: ${trade.size}{trade.timeframe && ` • ${trade.timeframe}`}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {trade.status === 'closed' && trade.pnl !== null && (
                      <div className="text-right">
                        <div className={`font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                        </div>
                        <div className={`text-xs ${trade.pnl_percent && trade.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {trade.pnl_percent && trade.pnl_percent >= 0 ? '+' : ''}{trade.pnl_percent?.toFixed(2)}%
                        </div>
                      </div>
                    )}
                    <div className="text-xs text-zinc-500">
                      {formatDate(trade.entry_date)}
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
                    {/* Trade details */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      {trade.stop_loss && (
                        <div>
                          <span className="text-zinc-400">Stop Loss:</span>
                          <span className="ml-2 text-red-400">${formatPrice(trade.stop_loss)}</span>
                        </div>
                      )}
                      {trade.take_profit && (
                        <div>
                          <span className="text-zinc-400">Take Profit:</span>
                          <span className="ml-2 text-green-400">${formatPrice(trade.take_profit)}</span>
                        </div>
                      )}
                      {trade.exit_price && (
                        <div>
                          <span className="text-zinc-400">Exit:</span>
                          <span className="ml-2 text-white">${formatPrice(trade.exit_price)}</span>
                        </div>
                      )}
                      {trade.timeframe && (
                        <div>
                          <span className="text-zinc-400">TF:</span>
                          <span className="ml-2 text-white">{trade.timeframe}</span>
                        </div>
                      )}
                    </div>

                    {/* Images & Notes - Side by Side */}
                    {(trade.image_url || trade.exit_image_url || trade.notes || trade.exit_notes) && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Entry Column */}
                        <div className="space-y-2">
                          {trade.image_url && (
                            <div>
                              <div className="text-xs text-zinc-500 mb-1">📈 Entrada</div>
                              <img
                                src={trade.image_url}
                                alt="Entry screenshot"
                                className="max-h-64 rounded-lg border border-zinc-700 cursor-pointer hover:opacity-80 transition-opacity"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setExpandedImage({ url: trade.image_url!, type: 'entry', tradeId: trade.id });
                                }}
                              />
                            </div>
                          )}
                          {trade.notes && (
                            <div className="text-sm text-zinc-300 bg-zinc-800/50 rounded p-3">
                              {trade.notes}
                            </div>
                          )}
                        </div>

                        {/* Exit Column */}
                        {(trade.exit_image_url || trade.exit_notes) && (
                          <div className="space-y-2">
                            {trade.exit_image_url && (
                              <div>
                                <div className="text-xs text-zinc-500 mb-1">📉 Cierre</div>
                                <img
                                  src={trade.exit_image_url}
                                  alt="Exit screenshot"
                                  className="max-h-64 rounded-lg border border-zinc-700 cursor-pointer hover:opacity-80 transition-opacity"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setExpandedImage({ url: trade.exit_image_url!, type: 'exit', tradeId: trade.id });
                                  }}
                                />
                              </div>
                            )}
                            {trade.exit_notes && (
                              <div className="text-sm text-zinc-300 bg-zinc-800/50 rounded p-3">
                                {trade.exit_notes}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2">
                      {trade.status === 'open' && (
                        <>
                          {showCloseForm === trade.id ? (
                            <div className="flex-1 space-y-3">
                              <div className="flex items-center gap-2">
                                <Input
                                  type="number"
                                  step="any"
                                  placeholder="Exit Price"
                                  value={closeData.exit_price}
                                  onChange={(e) => setCloseData({ ...closeData, exit_price: e.target.value })}
                                  className="bg-zinc-800 border-zinc-700 w-32"
                                />
                                <Input
                                  type="number"
                                  step="any"
                                  placeholder="Fees"
                                  value={closeData.fees}
                                  onChange={(e) => setCloseData({ ...closeData, fees: e.target.value })}
                                  className="bg-zinc-800 border-zinc-700 w-24"
                                />
                                <Button size="sm" onClick={() => handleClose(trade.id)}>
                                  <Check className="h-4 w-4" />
                                </Button>
                                <Button size="sm" variant="outline" onClick={() => {
                                  setShowCloseForm(null);
                                  setCloseData({ exit_price: '', fees: '', exit_notes: '', exit_image_url: '' });
                                }}>
                                  <X className="h-4 w-4" />
                                </Button>
                              </div>

                              {/* Exit Image Upload */}
                              <div
                                className="border-2 border-dashed border-zinc-700 rounded-lg p-3 text-center cursor-pointer hover:border-zinc-500 transition-colors"
                                onPaste={handleCloseImagePaste}
                                onClick={() => !closeData.exit_image_url && closeFileInputRef.current?.click()}
                              >
                                {closeData.exit_image_url ? (
                                  <div className="relative">
                                    <img
                                      src={closeData.exit_image_url}
                                      alt="Exit screenshot"
                                      className="max-h-32 mx-auto rounded"
                                    />
                                    <div className="absolute top-1 right-1 flex gap-1">
                                      <Button
                                        type="button"
                                        variant="secondary"
                                        size="icon"
                                        className="h-6 w-6"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setEditingImage({ source: 'closeForm', imageUrl: closeData.exit_image_url });
                                        }}
                                        title="Editar imagen"
                                      >
                                        <PenTool className="h-3 w-3" />
                                      </Button>
                                      <Button
                                        type="button"
                                        variant="destructive"
                                        size="icon"
                                        className="h-6 w-6"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setCloseData({ ...closeData, exit_image_url: '' });
                                        }}
                                      >
                                        <X className="h-3 w-3" />
                                      </Button>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="text-zinc-400 text-sm">
                                    <ImageIcon className="h-6 w-6 mx-auto mb-1" />
                                    <p>Pegar imagen de cierre (Ctrl+V)</p>
                                  </div>
                                )}
                                <input
                                  ref={closeFileInputRef}
                                  type="file"
                                  accept="image/*"
                                  onChange={handleCloseImageUpload}
                                  className="hidden"
                                />
                              </div>

                              {/* Exit Notes */}
                              <textarea
                                value={closeData.exit_notes}
                                onChange={(e) => setCloseData({ ...closeData, exit_notes: e.target.value })}
                                placeholder="Notas del cierre..."
                                className="w-full bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-md px-3 py-2 text-sm min-h-[60px]"
                              />
                            </div>
                          ) : (
                            <Button size="sm" variant="outline" onClick={() => setShowCloseForm(trade.id)}>
                              <DollarSign className="mr-2 h-4 w-4" />
                              Cerrar Trade
                            </Button>
                          )}
                        </>
                      )}
                      <Button size="sm" variant="outline" onClick={() => handleEdit(trade)}>
                        <Pencil className="mr-2 h-4 w-4" />
                        Editar
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleDelete(trade.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
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

      {/* Image Modal */}
      {expandedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90"
          onClick={() => setExpandedImage(null)}
        >
          {/* Close button */}
          <div className="absolute top-4 right-4 flex items-center gap-2 z-10">
            <Button
              variant="secondary"
              size="sm"
              className="text-white"
              onClick={(e) => {
                e.stopPropagation();
                setEditingImage({
                  source: expandedImage.type === 'entry' ? 'viewEntry' : 'viewExit',
                  imageUrl: expandedImage.url,
                  tradeId: expandedImage.tradeId,
                });
              }}
            >
              <PenTool className="h-4 w-4 mr-2" />
              Editar
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/20"
              onClick={() => setExpandedImage(null)}
            >
              <X className="h-6 w-6" />
            </Button>
          </div>

          {/* Image type indicator */}
          <div className="absolute top-4 left-4 text-white text-sm bg-black/50 px-3 py-1 rounded-full">
            {expandedImage.type === 'entry' ? '📈 Entrada' : '📉 Cierre'}
          </div>

          {/* Left arrow */}
          {canNavigate('prev') && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute left-4 top-1/2 -translate-y-1/2 text-white hover:bg-white/20 h-12 w-12"
              onClick={(e) => {
                e.stopPropagation();
                navigateImage('prev');
              }}
            >
              <ChevronLeft className="h-8 w-8" />
            </Button>
          )}

          {/* Image */}
          <img
            src={expandedImage.url}
            alt="Trade screenshot expanded"
            className="max-h-[90vh] max-w-[90vw] object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />

          {/* Right arrow */}
          {canNavigate('next') && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-4 top-1/2 -translate-y-1/2 text-white hover:bg-white/20 h-12 w-12"
              onClick={(e) => {
                e.stopPropagation();
                navigateImage('next');
              }}
            >
              <ChevronRight className="h-8 w-8" />
            </Button>
          )}

          {/* Navigation hint */}
          {(canNavigate('prev') || canNavigate('next')) && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/60 text-xs">
              Usá ← → para navegar
            </div>
          )}
        </div>
      )}

      {/* Image Editor Modal */}
      {editingImage && (
        <ImageEditor
          imageUrl={editingImage.imageUrl}
          isOpen={true}
          onSave={handleImageEditorSave}
          onCancel={() => setEditingImage(null)}
        />
      )}
    </div>
  );
}
