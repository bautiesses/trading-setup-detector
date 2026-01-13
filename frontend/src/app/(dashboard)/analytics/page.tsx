'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { Brain, Calendar, Loader2, ChevronDown, ChevronUp, Trash2 } from 'lucide-react';

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

interface SavedAnalysis {
  id: number;
  month: number;
  year: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  analysis_text: string;
  images_analyzed: number;
  created_at: string;
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
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([]);
  const [expandedAnalysis, setExpandedAnalysis] = useState<number | null>(null);
  const [loadingAnalyses, setLoadingAnalyses] = useState(true);

  // Load saved analyses on mount
  useEffect(() => {
    loadSavedAnalyses();
  }, []);

  const loadSavedAnalyses = async () => {
    try {
      const data = await api.getMonthlyAnalyses() as { analyses: SavedAnalysis[]; total: number };
      setSavedAnalyses(data.analyses || []);
    } catch (error) {
      console.error('Error loading analyses:', error);
    } finally {
      setLoadingAnalyses(false);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const data = await api.analyzeMonth(selectedMonth, selectedYear) as AnalysisResult;

      // Si el análisis fue exitoso, guardarlo automáticamente
      if (data.success && data.analysis) {
        await api.saveMonthlyAnalysis({
          month: data.month!,
          year: data.year!,
          total_trades: data.total_trades || 0,
          winning_trades: data.winning_trades || 0,
          losing_trades: data.losing_trades || 0,
          win_rate: data.win_rate || 0,
          total_pnl: 0,
          analysis_text: data.analysis,
          images_analyzed: data.images_analyzed || 0,
        });
        await loadSavedAnalyses();
        // Expandir el análisis recién creado
        const newAnalyses = await api.getMonthlyAnalyses() as { analyses: SavedAnalysis[]; total: number };
        const justSaved = newAnalyses.analyses.find(a => a.month === data.month && a.year === data.year);
        if (justSaved) {
          setExpandedAnalysis(justSaved.id);
        }
      } else {
        // Solo mostrar error si falló
        setResult(data);
      }
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Error al analizar'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAnalysis = async (id: number) => {
    if (!confirm('¿Eliminar este análisis?')) return;
    try {
      await api.deleteMonthlyAnalysis(id);
      setSavedAnalyses(savedAnalyses.filter(a => a.id !== id));
      if (expandedAnalysis === id) setExpandedAnalysis(null);
    } catch (error) {
      console.error('Error deleting analysis:', error);
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

      {/* Error Display */}
      {result && !result.success && (
        <Card className="border-red-500/30">
          <CardContent className="py-8 text-center">
            <p className="text-red-400">{result.error}</p>
          </CardContent>
        </Card>
      )}

      {/* Saved Analyses */}
      {savedAnalyses.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xl font-semibold text-white">Análisis Guardados</h2>
          {savedAnalyses.map((analysis) => (
            <Card
              key={analysis.id}
              className={`border-l-4 ${
                analysis.win_rate >= 50 ? 'border-l-green-500' : 'border-l-red-500'
              } cursor-pointer hover:bg-zinc-800/50 transition-colors`}
            >
              <CardContent className="py-3">
                <div
                  className="flex items-center justify-between"
                  onClick={() => setExpandedAnalysis(expandedAnalysis === analysis.id ? null : analysis.id)}
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <span className="font-bold text-white text-lg">
                        {MONTHS[analysis.month - 1]} {analysis.year}
                      </span>
                      <div className="text-xs text-zinc-400 mt-1">
                        {analysis.total_trades} trades • {analysis.winning_trades}W / {analysis.losing_trades}L
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className={`font-bold ${analysis.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                        {analysis.win_rate.toFixed(1)}% WR
                      </div>
                      <div className="text-xs text-zinc-500">
                        {analysis.images_analyzed} imgs
                      </div>
                    </div>
                    {expandedAnalysis === analysis.id ? (
                      <ChevronUp className="h-5 w-5 text-zinc-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-zinc-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Content */}
                {expandedAnalysis === analysis.id && (
                  <div className="mt-4 pt-4 border-t border-zinc-700">
                    <div className="prose prose-invert prose-sm max-w-none mb-4">
                      <div className="whitespace-pre-wrap text-zinc-300 leading-relaxed">
                        {analysis.analysis_text}
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-zinc-500">
                        Guardado: {new Date(analysis.created_at).toLocaleDateString('es-AR')}
                      </span>
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteAnalysis(analysis.id);
                        }}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Eliminar
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!result && !loading && savedAnalyses.length === 0 && !loadingAnalyses && (
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

      {/* Loading Analyses */}
      {loadingAnalyses && (
        <Card>
          <CardContent className="py-8 text-center">
            <Loader2 className="h-8 w-8 text-zinc-400 animate-spin mx-auto" />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
