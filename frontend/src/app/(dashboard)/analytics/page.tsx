'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { Brain, TrendingUp, TrendingDown, Calendar, Loader2 } from 'lucide-react';

interface AnalysisResult {
  success: boolean;
  month?: number;
  year?: number;
  total_trades?: number;
  winning_trades?: number;
  losing_trades?: number;
  win_rate?: number;
  images_analyzed?: number;
  analysis?: string;
  error?: string;
}

const MONTHS = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

export default function AnalyticsPage() {
  const currentDate = new Date();
  const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear());
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await api.analyzeMonth(selectedMonth, selectedYear) as AnalysisResult;
      setResult(data);
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Error al analizar'
      });
    } finally {
      setLoading(false);
    }
  };

  // Generate year options (current year and 2 years back)
  const years = Array.from({ length: 3 }, (_, i) => currentDate.getFullYear() - i);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Brain className="h-8 w-8 text-purple-400" />
          Análisis con IA
        </h1>
      </div>

      {/* Month/Year Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Seleccionar Período
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div>
              <label className="text-xs text-zinc-400 block mb-1">Mes</label>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                className="bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg px-3 py-2"
              >
                {MONTHS.map((month, i) => (
                  <option key={i} value={i + 1}>{month}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-zinc-400 block mb-1">Año</label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-lg px-3 py-2"
              >
                {years.map((year) => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>
            <div className="flex-1" />
            <Button
              onClick={handleAnalyze}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analizando...
                </>
              ) : (
                <>
                  <Brain className="mr-2 h-4 w-4" />
                  Analizar con IA
                </>
              )}
            </Button>
          </div>
          {loading && (
            <p className="text-sm text-zinc-400 mt-3">
              Claude está analizando tus trades y screenshots. Esto puede tomar unos segundos...
            </p>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <>
          {result.success ? (
            <>
              {/* Stats Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="bg-zinc-900/50">
                  <CardContent className="p-4">
                    <p className="text-xs text-zinc-500 mb-1">Total Trades</p>
                    <p className="text-2xl font-bold text-white">{result.total_trades}</p>
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900/50">
                  <CardContent className="p-4">
                    <p className="text-xs text-zinc-500 mb-1">Ganadores</p>
                    <p className="text-2xl font-bold text-green-400 flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      {result.winning_trades}
                    </p>
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900/50">
                  <CardContent className="p-4">
                    <p className="text-xs text-zinc-500 mb-1">Perdedores</p>
                    <p className="text-2xl font-bold text-red-400 flex items-center gap-2">
                      <TrendingDown className="h-5 w-5" />
                      {result.losing_trades}
                    </p>
                  </CardContent>
                </Card>
                <Card className="bg-zinc-900/50">
                  <CardContent className="p-4">
                    <p className="text-xs text-zinc-500 mb-1">Win Rate</p>
                    <p className={`text-2xl font-bold ${(result.win_rate || 0) >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                      {result.win_rate?.toFixed(1)}%
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* AI Analysis */}
              <Card className="border-purple-500/30">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-purple-400">
                    <Brain className="h-5 w-5" />
                    Análisis de Claude
                    {result.images_analyzed && result.images_analyzed > 0 && (
                      <span className="text-xs text-zinc-500 font-normal ml-2">
                        ({result.images_analyzed} imágenes analizadas)
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-invert prose-sm max-w-none">
                    <div className="whitespace-pre-wrap text-zinc-300 leading-relaxed">
                      {result.analysis}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="border-red-500/30">
              <CardContent className="py-8 text-center">
                <p className="text-red-400">{result.error}</p>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Empty State */}
      {!result && !loading && (
        <Card>
          <CardContent className="py-12 text-center">
            <Brain className="h-16 w-16 text-zinc-700 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-zinc-300 mb-2">
              Análisis Inteligente de Trades
            </h3>
            <p className="text-zinc-500 max-w-md mx-auto">
              Seleccioná un mes y año para que Claude analice tus trades cerrados,
              incluyendo los screenshots de los charts. Recibirás insights sobre
              qué setups funcionaron mejor y qué patrones evitar.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
