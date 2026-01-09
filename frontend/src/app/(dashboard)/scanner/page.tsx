'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { Play, TrendingUp, TrendingDown, RefreshCw, Trash2, BarChart3, Power, Bell, BellOff } from 'lucide-react';
import { SignalChart } from '@/components/charts/SignalChart';

interface ScanResult {
  id: number;
  symbol: string;
  timeframe: string;
  pattern_type: 'bullish_retest' | 'bearish_retest';
  level_price: number;
  current_price: number;
  confidence_score: number;
  is_match: boolean;
  message: string;
  created_at: string;
}

interface ScannerStatus {
  symbols_monitored: number;
  scans_today: number;
  signals_today: number;
  last_scan: string | null;
  is_running: boolean;
}

interface AutoScannerStatus {
  is_running: boolean;
  interval_minutes: number;
  last_scan: string | null;
}

export default function ScannerPage() {
  const [status, setStatus] = useState<ScannerStatus | null>(null);
  const [results, setResults] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [sensitivity, setSensitivity] = useState('medium');
  const [selectedSignal, setSelectedSignal] = useState<ScanResult | null>(null);

  // Auto scanner state
  const [autoStatus, setAutoStatus] = useState<AutoScannerStatus | null>(null);
  const [scanInterval, setScanInterval] = useState(5);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [newSignalCount, setNewSignalCount] = useState(0);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Initialize audio
  useEffect(() => {
    audioRef.current = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2teleRoAQJ/markup...');
    // Simple beep sound
    audioRef.current = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
  }, []);

  // Request notification permission
  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setNotificationsEnabled(permission === 'granted');
    }
  };

  // Show notification
  const showNotification = useCallback((signal: ScanResult) => {
    if (notificationsEnabled && 'Notification' in window && Notification.permission === 'granted') {
      const title = signal.pattern_type === 'bullish_retest' ? '🟢 Señal COMPRA' : '🔴 Señal VENTA';
      const body = `${signal.symbol} (${signal.timeframe}) - Nivel: $${signal.level_price.toFixed(2)}`;

      new Notification(title, {
        body,
        icon: signal.pattern_type === 'bullish_retest' ? '/bull.png' : '/bear.png',
        tag: `signal-${signal.id}`,
      });
    }

    // Play sound
    if (audioRef.current) {
      audioRef.current.play().catch(() => {});
    }
  }, [notificationsEnabled]);

  // Fetch initial data
  useEffect(() => {
    fetchData();
    fetchAutoStatus();
  }, []);

  // Poll for new signals when auto scanner is running
  useEffect(() => {
    if (autoStatus?.is_running) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const response = await api.getNewSignals() as { signals: ScanResult[]; count: number };
          if (response.count > 0) {
            setNewSignalCount(prev => prev + response.count);
            // Show notification for each new signal
            response.signals.forEach((signal: ScanResult) => showNotification(signal));
            // Refresh results
            fetchData();
          }
        } catch (error) {
          console.error('Error polling for signals:', error);
        }
      }, 10000); // Poll every 10 seconds
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [autoStatus?.is_running, showNotification]);

  const fetchData = async () => {
    try {
      const [statusData, resultsData] = await Promise.all([
        api.getScannerStatus(),
        api.getScanResults(),
      ]);
      setStatus(statusData as ScannerStatus);
      setResults((resultsData as { results: ScanResult[] }).results || []);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAutoStatus = async () => {
    try {
      const data = await api.getAutoScannerStatus() as AutoScannerStatus;
      setAutoStatus(data);
      if (data.interval_minutes) {
        setScanInterval(data.interval_minutes);
      }
    } catch (error) {
      console.error('Error fetching auto status:', error);
    }
  };

  const toggleAutoScanner = async () => {
    try {
      if (autoStatus?.is_running) {
        await api.stopAutoScanner();
      } else {
        await api.startAutoScanner(scanInterval);
        // Request notification permission when starting
        requestNotificationPermission();
      }
      await fetchAutoStatus();
      setNewSignalCount(0);
    } catch (error) {
      console.error('Error toggling auto scanner:', error);
    }
  };

  const runScan = async () => {
    setScanning(true);
    try {
      const response = await api.runManualScan(sensitivity) as { results: ScanResult[], signals_found: number };
      setResults(response.results || []);
      fetchData();
    } catch (error) {
      console.error('Error running scan:', error);
    } finally {
      setScanning(false);
    }
  };

  const clearResults = async () => {
    if (!confirm('¿Eliminar todos los resultados antiguos?')) return;
    try {
      await api.clearScanResults();
      fetchData();
      setNewSignalCount(0);
    } catch (error) {
      console.error('Error clearing results:', error);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('es-AR');
  };

  const formatPrice = (price: number) => {
    if (price >= 1) return price.toFixed(2);
    if (price >= 0.01) return price.toFixed(4);
    return price.toFixed(6);
  };

  if (loading) {
    return <div className="min-h-screen" />;
  }

  const bullishSignals = results.filter(r => r.pattern_type === 'bullish_retest');
  const bearishSignals = results.filter(r => r.pattern_type === 'bearish_retest');

  return (
    <div className="space-y-6">
      {/* Modal del gráfico */}
      {selectedSignal && (
        <SignalChart
          symbol={selectedSignal.symbol}
          timeframe={selectedSignal.timeframe}
          levelPrice={selectedSignal.level_price}
          patternType={selectedSignal.pattern_type}
          onClose={() => setSelectedSignal(null)}
        />
      )}

      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            Break & Retest Scanner
            {autoStatus?.is_running && (
              <span className="flex items-center gap-2">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
                <span className="text-sm font-normal text-green-400">Auto ON</span>
              </span>
            )}
            {newSignalCount > 0 && (
              <Badge className="bg-red-500 text-white animate-pulse">
                {newSignalCount} nuevas
              </Badge>
            )}
          </h1>
          <p className="text-zinc-400 mt-1">Detecta patrones de ruptura y retesteo automáticamente</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {/* Notification toggle */}
          <Button
            variant="outline"
            size="icon"
            onClick={requestNotificationPermission}
            title={notificationsEnabled ? 'Notificaciones activadas' : 'Activar notificaciones'}
          >
            {notificationsEnabled ? (
              <Bell className="h-4 w-4 text-green-400" />
            ) : (
              <BellOff className="h-4 w-4" />
            )}
          </Button>

          {/* Auto scanner controls */}
          <div className="flex items-center gap-2 bg-zinc-800 rounded-lg p-1">
            <select
              value={scanInterval}
              onChange={(e) => setScanInterval(Number(e.target.value))}
              disabled={autoStatus?.is_running}
              className="bg-transparent border-none text-zinc-100 text-sm px-2 py-1 focus:outline-none"
            >
              <option value={1}>1 min</option>
              <option value={2}>2 min</option>
              <option value={5}>5 min</option>
              <option value={10}>10 min</option>
              <option value={15}>15 min</option>
              <option value={30}>30 min</option>
            </select>
            <Button
              onClick={toggleAutoScanner}
              variant={autoStatus?.is_running ? 'destructive' : 'default'}
              size="sm"
            >
              <Power className="mr-2 h-4 w-4" />
              {autoStatus?.is_running ? 'Detener Auto' : 'Auto Scan'}
            </Button>
          </div>

          <select
            value={sensitivity}
            onChange={(e) => setSensitivity(e.target.value)}
            className="bg-zinc-800 border border-zinc-600 text-zinc-100 rounded-lg px-3 py-2 text-sm"
          >
            <option value="low">Baja sensibilidad</option>
            <option value="medium">Media sensibilidad</option>
            <option value="high">Alta sensibilidad</option>
          </select>
          <Button onClick={runScan} disabled={scanning}>
            {scanning ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Escaneando...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Escanear Ahora
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Auto Scanner Status Card */}
      {autoStatus?.is_running && (
        <Card className="border-green-500/50 bg-green-500/10">
          <CardContent className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </div>
                <span className="text-green-400 font-medium">
                  Scanner automático activo - cada {autoStatus.interval_minutes} minutos
                </span>
              </div>
              {autoStatus.last_scan && (
                <span className="text-zinc-400 text-sm">
                  Último scan: {formatDate(autoStatus.last_scan)}
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-white">{status?.symbols_monitored || 0}</div>
            <p className="text-zinc-400 text-sm">Símbolos monitoreados</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-white">{status?.scans_today || 0}</div>
            <p className="text-zinc-400 text-sm">Scans hoy</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-400">{bullishSignals.length}</div>
            <p className="text-zinc-400 text-sm">Señales Bullish 🟢</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-red-400">{bearishSignals.length}</div>
            <p className="text-zinc-400 text-sm">Señales Bearish 🔴</p>
          </CardContent>
        </Card>
      </div>

      {/* Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="bg-blue-500/20 p-3 rounded-lg">
              <TrendingUp className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-white">¿Cómo funciona?</h3>
              <p className="text-zinc-400 text-sm mt-1">
                El scanner busca niveles de soporte/resistencia que fueron rotos y ahora están siendo
                retesteados. <strong className="text-green-400">Bullish</strong>: resistencia rota → ahora soporte.
                <strong className="text-red-400"> Bearish</strong>: soporte roto → ahora resistencia.
                <br />
                <span className="text-blue-400">Haz clic en una señal para ver el gráfico con el nivel marcado.</span>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Señales Detectadas</h2>
        {results.length > 0 && (
          <Button variant="outline" size="sm" onClick={clearResults}>
            <Trash2 className="mr-2 h-4 w-4" />
            Limpiar
          </Button>
        )}
      </div>

      {results.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-zinc-400 mb-4">
              No hay señales detectadas. Agrega símbolos a tu watchlist y ejecuta un scan.
            </p>
            <Button onClick={runScan} disabled={scanning}>
              <Play className="mr-2 h-4 w-4" />
              Ejecutar Scan
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {results.map((result) => (
            <Card
              key={result.id}
              className={`border-l-4 cursor-pointer transition-all hover:scale-[1.01] hover:shadow-lg ${
                result.pattern_type === 'bullish_retest'
                  ? 'border-l-green-500 hover:border-l-green-400'
                  : 'border-l-red-500 hover:border-l-red-400'
              }`}
              onClick={() => setSelectedSignal(result)}
            >
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${
                      result.pattern_type === 'bullish_retest'
                        ? 'bg-green-500/20'
                        : 'bg-red-500/20'
                    }`}>
                      {result.pattern_type === 'bullish_retest' ? (
                        <TrendingUp className="h-5 w-5 text-green-400" />
                      ) : (
                        <TrendingDown className="h-5 w-5 text-red-400" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-lg">{result.symbol}</span>
                        <Badge variant="secondary">{result.timeframe}</Badge>
                        <Badge variant={result.pattern_type === 'bullish_retest' ? 'success' : 'destructive'}>
                          {result.pattern_type === 'bullish_retest' ? '🟢 COMPRA' : '🔴 VENTA'}
                        </Badge>
                      </div>
                      <p className="text-zinc-400 text-sm mt-1">
                        Nivel: <span className="text-white">${formatPrice(result.level_price)}</span>
                        {' → '}
                        Precio actual: <span className="text-white">${formatPrice(result.current_price)}</span>
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-sm text-zinc-400">
                        Fuerza: {Math.round(result.confidence_score * 10)} toques
                      </div>
                      <div className="text-xs text-zinc-500 mt-1">
                        {formatDate(result.created_at)}
                      </div>
                    </div>
                    <div className="bg-zinc-800 p-2 rounded-lg">
                      <BarChart3 className="h-5 w-5 text-blue-400" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {status?.last_scan && (
        <p className="text-center text-zinc-500 text-sm">
          Último scan: {formatDate(status.last_scan)}
        </p>
      )}
    </div>
  );
}
