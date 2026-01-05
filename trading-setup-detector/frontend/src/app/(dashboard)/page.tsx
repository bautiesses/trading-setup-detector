'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { Play, TrendingUp, TrendingDown, List, ScanSearch } from 'lucide-react';
import Link from 'next/link';

interface ScannerStatus {
  symbols_monitored: number;
  scans_today: number;
  signals_today: number;
  last_scan: string | null;
}

interface ScanResult {
  id: number;
  symbol: string;
  timeframe: string;
  pattern_type: string;
  level_price: number;
  current_price: number;
  created_at: string;
}

export default function DashboardPage() {
  const [status, setStatus] = useState<ScannerStatus | null>(null);
  const [recentSignals, setRecentSignals] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statusData, resultsData] = await Promise.all([
        api.getScannerStatus(),
        api.getScanResults(),
      ]);
      setStatus(statusData as ScannerStatus);
      setRecentSignals(((resultsData as { results: ScanResult[] }).results || []).slice(0, 5));
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    if (price >= 1) return price.toFixed(2);
    if (price >= 0.01) return price.toFixed(4);
    return price.toFixed(6);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (minutes < 60) return `Hace ${minutes} min`;
    if (hours < 24) return `Hace ${hours}h`;
    return date.toLocaleDateString('es-AR');
  };

  if (loading) {
    return <div className="min-h-screen" />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-zinc-400 mt-1">Break & Retest Scanner - 100% Gratis</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Símbolos Monitoreados</CardTitle>
            <List className="h-4 w-4 text-zinc-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{status?.symbols_monitored || 0}</div>
            <Link href="/watchlist" className="text-xs text-blue-400 hover:underline">
              Configurar watchlist →
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Scans Hoy</CardTitle>
            <ScanSearch className="h-4 w-4 text-zinc-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{status?.scans_today || 0}</div>
            <p className="text-xs text-zinc-500">
              {status?.last_scan ? `Último: ${formatDate(status.last_scan)}` : 'Sin scans'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Señales Hoy</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{status?.signals_today || 0}</div>
            <Link href="/scanner" className="text-xs text-blue-400 hover:underline">
              Ver todas →
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-white">Acciones Rápidas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Link href="/scanner">
              <Button>
                <Play className="mr-2 h-4 w-4" />
                Ejecutar Scan
              </Button>
            </Link>
            <Link href="/watchlist">
              <Button variant="outline">
                <List className="mr-2 h-4 w-4" />
                Agregar Símbolos
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Recent Signals */}
      <Card>
        <CardHeader>
          <CardTitle className="text-white">Señales Recientes</CardTitle>
        </CardHeader>
        <CardContent>
          {recentSignals.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-zinc-400 mb-4">No hay señales todavía</p>
              <p className="text-zinc-500 text-sm">
                Agrega símbolos a tu watchlist y ejecuta un scan para detectar patrones de Break & Retest
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentSignals.map((signal) => (
                <div
                  key={signal.id}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    signal.pattern_type === 'bullish_retest'
                      ? 'border-green-500/30 bg-green-500/10'
                      : 'border-red-500/30 bg-red-500/10'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {signal.pattern_type === 'bullish_retest' ? (
                      <TrendingUp className="h-5 w-5 text-green-400" />
                    ) : (
                      <TrendingDown className="h-5 w-5 text-red-400" />
                    )}
                    <div>
                      <span className="font-semibold text-white">{signal.symbol}</span>
                      <span className="text-zinc-400 text-sm ml-2">{signal.timeframe}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-medium ${
                      signal.pattern_type === 'bullish_retest' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {signal.pattern_type === 'bullish_retest' ? '🟢 COMPRA' : '🔴 VENTA'}
                    </div>
                    <div className="text-xs text-zinc-500">${formatPrice(signal.level_price)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* How it works */}
      <Card>
        <CardHeader>
          <CardTitle className="text-white">¿Cómo funciona?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-semibold text-green-400 flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Bullish Retest (COMPRA)
              </h3>
              <div className="text-zinc-400 text-sm space-y-2">
                <p>1. El precio rompe una resistencia hacia arriba</p>
                <p>2. La resistencia ahora se convierte en soporte</p>
                <p>3. El precio vuelve a testear el nivel</p>
                <p>4. <span className="text-green-400">→ Oportunidad de compra</span></p>
              </div>
            </div>
            <div className="space-y-4">
              <h3 className="font-semibold text-red-400 flex items-center gap-2">
                <TrendingDown className="h-5 w-5" />
                Bearish Retest (VENTA)
              </h3>
              <div className="text-zinc-400 text-sm space-y-2">
                <p>1. El precio rompe un soporte hacia abajo</p>
                <p>2. El soporte ahora se convierte en resistencia</p>
                <p>3. El precio vuelve a testear el nivel</p>
                <p>4. <span className="text-red-400">→ Oportunidad de venta</span></p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
