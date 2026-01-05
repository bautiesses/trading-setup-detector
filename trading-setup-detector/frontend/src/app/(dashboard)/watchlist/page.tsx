'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api';
import { WatchlistItem, Symbol } from '@/types';
import { TIMEFRAMES } from '@/lib/utils';
import { Plus, Trash2, X } from 'lucide-react';

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>(['1h', '4h']);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [watchlistData, symbolsData] = await Promise.all([
        api.getWatchlist(),
        api.getSymbols(),
      ]);
      setItems((watchlistData as { items: WatchlistItem[] }).items || []);
      setSymbols((symbolsData as { symbols: Symbol[] }).symbols || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (selectedSymbols.length === 0 || selectedTimeframes.length === 0) return;

    setAdding(true);
    try {
      // Add all selected symbols
      await Promise.all(
        selectedSymbols.map(symbol => api.addToWatchlist(symbol, selectedTimeframes))
      );
      setShowAdd(false);
      setSelectedSymbols([]);
      setSelectedTimeframes(['1h', '4h']);
      setSearch('');
      fetchData();
    } catch (error) {
      console.error('Error adding to watchlist:', error);
    } finally {
      setAdding(false);
    }
  };

  const toggleSymbol = (symbol: string) => {
    setSelectedSymbols(prev =>
      prev.includes(symbol)
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const selectAllFiltered = () => {
    const filtered = filteredSymbols.slice(0, 50).map(s => s.symbol);
    setSelectedSymbols(prev => {
      const newSymbols = filtered.filter(s => !prev.includes(s));
      return [...prev, ...newSymbols];
    });
  };

  const clearSelection = () => {
    setSelectedSymbols([]);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Remove this symbol from watchlist?')) return;

    try {
      await api.removeFromWatchlist(id);
      fetchData();
    } catch (error) {
      console.error('Error removing from watchlist:', error);
    }
  };

  const handleToggleActive = async (item: WatchlistItem) => {
    try {
      await api.updateWatchlistItem(item.id, { is_active: !item.is_active });
      fetchData();
    } catch (error) {
      console.error('Error toggling item:', error);
    }
  };

  const toggleTimeframe = (tf: string) => {
    setSelectedTimeframes((prev) =>
      prev.includes(tf)
        ? prev.filter((t) => t !== tf)
        : [...prev, tf]
    );
  };

  const filteredSymbols = symbols.filter((s) =>
    s.symbol.toLowerCase().includes(search.toLowerCase()) ||
    s.base_asset.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return <div className="min-h-screen" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Watchlist</h1>
        <Button onClick={() => setShowAdd(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Symbol
        </Button>
      </div>

      {/* Add Symbol Modal */}
      {showAdd && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-lg mx-4">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Add Symbol to Watchlist</CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setShowAdd(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-200">Search Symbol</label>
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search for a symbol..."
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-zinc-200">Select Symbols</label>
                  <div className="flex gap-2">
                    <button
                      onClick={selectAllFiltered}
                      className="text-xs text-blue-400 hover:text-blue-300"
                    >
                      Select all
                    </button>
                    {selectedSymbols.length > 0 && (
                      <button
                        onClick={clearSelection}
                        className="text-xs text-red-400 hover:text-red-300"
                      >
                        Clear ({selectedSymbols.length})
                      </button>
                    )}
                  </div>
                </div>
                <div className="max-h-64 overflow-y-auto border border-zinc-700 rounded-lg bg-zinc-800">
                  {filteredSymbols.slice(0, 100).map((symbol) => (
                    <button
                      key={symbol.symbol}
                      onClick={() => toggleSymbol(symbol.symbol)}
                      className={`w-full px-3 py-2 text-left text-sm flex justify-between items-center transition-colors ${
                        selectedSymbols.includes(symbol.symbol)
                          ? 'bg-blue-600 text-white'
                          : 'hover:bg-zinc-700 text-zinc-100'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <div className={`w-4 h-4 border rounded flex items-center justify-center ${
                          selectedSymbols.includes(symbol.symbol)
                            ? 'bg-blue-500 border-blue-500'
                            : 'border-zinc-500'
                        }`}>
                          {selectedSymbols.includes(symbol.symbol) && (
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                        <span>{symbol.symbol}</span>
                      </div>
                      <span className={selectedSymbols.includes(symbol.symbol) ? 'text-blue-200' : 'text-zinc-400'}>{symbol.base_asset}</span>
                    </button>
                  ))}
                </div>
                {selectedSymbols.length > 0 && (
                  <p className="text-sm text-blue-400">{selectedSymbols.length} selected</p>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-200">Timeframes</label>
                <div className="flex flex-wrap gap-2">
                  {TIMEFRAMES.map((tf) => (
                    <button
                      key={tf.value}
                      onClick={() => toggleTimeframe(tf.value)}
                      className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                        selectedTimeframes.includes(tf.value)
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'border-zinc-600 text-zinc-300 hover:bg-zinc-700 hover:border-zinc-500'
                      }`}
                    >
                      {tf.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => { setShowAdd(false); setSelectedSymbols([]); setSearch(''); }}>
                  Cancel
                </Button>
                <Button
                  onClick={handleAdd}
                  disabled={selectedSymbols.length === 0 || selectedTimeframes.length === 0 || adding}
                >
                  {adding ? 'Adding...' : `Add ${selectedSymbols.length > 0 ? selectedSymbols.length : ''} to Watchlist`}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Watchlist Table */}
      {items.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-zinc-400 mb-4">
              Your watchlist is empty. Add symbols to monitor!
            </p>
            <Button onClick={() => setShowAdd(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Symbol
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between border-b border-zinc-700 pb-4 last:border-0"
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="font-semibold">{item.symbol}</p>
                      <div className="flex gap-1 mt-1">
                        {item.timeframes.map((tf) => (
                          <Badge key={tf} variant="secondary" className="text-xs">
                            {tf}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={item.is_active ? 'success' : 'secondary'}>
                      {item.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggleActive(item)}
                    >
                      {item.is_active ? 'Disable' : 'Enable'}
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(item.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
