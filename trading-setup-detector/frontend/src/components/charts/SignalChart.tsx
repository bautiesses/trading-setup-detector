'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, ColorType, IChartApi, LineStyle, Time, CandlestickSeries } from 'lightweight-charts';
import { api } from '@/lib/api';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SignalChartProps {
  symbol: string;
  timeframe: string;
  levelPrice: number;
  patternType: 'bullish_retest' | 'bearish_retest';
  onClose: () => void;
}

interface KlineData {
  open_time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface KlinesResponse {
  symbol: string;
  interval: string;
  klines: KlineData[];
}

export function SignalChart({ symbol, timeframe, levelPrice, patternType, onClose }: SignalChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initChart = useCallback(async () => {
    if (!chartContainerRef.current) return;

    // Limpiar chart anterior si existe
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    try {
      // Cargar datos primero
      const response = await api.getKlines(symbol, timeframe, 200) as KlinesResponse;
      const klines = response.klines || [];

      if (klines.length === 0) {
        setError('No hay datos disponibles para este símbolo');
        setLoading(false);
        return;
      }

      // Crear el chart solo si tenemos datos
      const chart = createChart(chartContainerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: '#09090b' },
          textColor: '#a1a1aa',
        },
        grid: {
          vertLines: { color: '#27272a' },
          horzLines: { color: '#27272a' },
        },
        width: chartContainerRef.current.clientWidth,
        height: 300,
        crosshair: {
          mode: 1,
          vertLine: {
            color: '#52525b',
            labelBackgroundColor: '#18181b',
          },
          horzLine: {
            color: '#52525b',
            labelBackgroundColor: '#18181b',
          },
        },
        timeScale: {
          borderColor: '#3f3f46',
          timeVisible: true,
          secondsVisible: false,
        },
        rightPriceScale: {
          borderColor: '#3f3f46',
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        },
      });

      chartRef.current = chart;

      // Crear serie de velas
      const candlestickSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#22c55e',
        downColor: '#ef4444',
        borderUpColor: '#22c55e',
        borderDownColor: '#ef4444',
        wickUpColor: '#22c55e',
        wickDownColor: '#ef4444',
      });

      // Convertir datos de klines a formato del chart
      const chartData = klines.map((k: KlineData) => ({
        time: Math.floor(k.open_time / 1000) as Time,
        open: k.open,
        high: k.high,
        low: k.low,
        close: k.close,
      }));

      candlestickSeries.setData(chartData);

      // Agregar marca de precio en el nivel
      const levelColor = patternType === 'bullish_retest' ? '#22c55e' : '#ef4444';

      candlestickSeries.createPriceLine({
        price: levelPrice,
        color: levelColor,
        lineWidth: 2,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: patternType === 'bullish_retest' ? 'Soporte' : 'Resistencia',
      });

      chart.timeScale().fitContent();
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error('Error loading chart data:', err);
      setError(err instanceof Error ? err.message : 'Error al cargar datos del gráfico');
      setLoading(false);
    }
  }, [symbol, timeframe, levelPrice, patternType]);

  useEffect(() => {
    initChart();

    // Manejar resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [initChart]);

  // Cerrar con Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-zinc-900 rounded-xl w-full max-w-3xl border border-zinc-700 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-700">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              {symbol}
              <span className="text-zinc-400 text-sm font-normal">({timeframe})</span>
              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                patternType === 'bullish_retest'
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-red-500/20 text-red-400'
              }`}>
                {patternType === 'bullish_retest' ? '🟢 COMPRA' : '🔴 VENTA'}
              </span>
            </h3>
            <p className="text-zinc-400 text-sm mt-1">
              Nivel detectado: <span className="text-white font-medium">${levelPrice.toFixed(levelPrice >= 1 ? 2 : 6)}</span>
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Chart */}
        <div className="p-3">
          {loading && (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-zinc-400">Cargando gráfico...</div>
            </div>
          )}
          {error && (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-red-400">{error}</div>
            </div>
          )}
          <div
            ref={chartContainerRef}
            className={`w-full ${loading || error ? 'hidden' : ''}`}
          />
        </div>

        {/* Footer con info */}
        <div className="px-4 py-3 border-t border-zinc-700 bg-zinc-800/50 rounded-b-xl">
          <p className="text-xs text-zinc-300">
            {patternType === 'bullish_retest' ? (
              <>
                <strong className="text-green-400">Break & Retest Alcista:</strong> Resistencia rota → ahora soporte. Oportunidad de compra.
              </>
            ) : (
              <>
                <strong className="text-red-400">Break & Retest Bajista:</strong> Soporte roto → ahora resistencia. Oportunidad de venta.
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
