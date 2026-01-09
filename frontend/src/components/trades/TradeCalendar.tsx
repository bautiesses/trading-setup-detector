'use client';

import { useState, useMemo, useRef, useEffect } from 'react';
import { ChevronLeft, ChevronRight, TrendingUp, TrendingDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

interface Trade {
  id: number;
  symbol: string;
  side: string;
  pnl: number | null;
  exit_date: string | null;
  status: string;
}

interface TradeCalendarProps {
  trades: Trade[];
}

const DAYS_OF_WEEK = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
const MONTHS = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

export function TradeCalendar({ trades }: TradeCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  const currentMonth = currentDate.getMonth();
  const currentYear = currentDate.getFullYear();

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setSelectedDay(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Group trades by day
  const tradesByDay = useMemo(() => {
    const result: Record<string, Trade[]> = {};

    trades.forEach((trade) => {
      if (trade.status === 'closed' && trade.exit_date && trade.pnl !== null) {
        const exitDate = new Date(trade.exit_date);
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

  // Navigate months
  const prevMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth - 1, 1));
    setSelectedDay(null);
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentYear, currentMonth + 1, 1));
    setSelectedDay(null);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
    setSelectedDay(null);
  };

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const days = [];

    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push({ day: null, profit: null, trades: [] as Trade[] });
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
            <button
              onClick={goToToday}
              className="text-xs font-medium text-white min-w-[80px] hover:text-blue-400 transition-colors"
            >
              {MONTHS[currentMonth].slice(0, 3)} {currentYear}
            </button>
            <Button variant="ghost" size="icon" className="h-5 w-5" onClick={nextMonth}>
              <ChevronRight className="h-3 w-3" />
            </Button>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className={monthlyStats.totalProfit >= 0 ? 'text-green-400' : 'text-red-400'}>
              {monthlyStats.totalProfit >= 0 ? '+' : ''}${monthlyStats.totalProfit.toFixed(0)}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="px-2 pb-2 pt-0">
        {/* Days of week header */}
        <div className="grid grid-cols-7 gap-0.5 mb-0.5">
          {DAYS_OF_WEEK.map((day) => (
            <div key={day} className="text-center text-[9px] text-zinc-600 w-9">
              {day.charAt(0)}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
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

        {/* Selected day trades popover */}
        {selectedDay && selectedDayTrades.length > 0 && (
          <div className="mt-2 pt-2 border-t border-zinc-800">
            <p className="text-[10px] text-zinc-500 mb-1.5">{selectedDay} de {MONTHS[currentMonth]}</p>
            <div className="space-y-1">
              {selectedDayTrades.map((trade) => (
                <div key={trade.id} className="flex items-center justify-between text-[11px] bg-zinc-800/50 rounded px-2 py-1">
                  <div className="flex items-center gap-1.5">
                    {trade.side === 'long' ? (
                      <TrendingUp className="h-3 w-3 text-green-400" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-red-400" />
                    )}
                    <span className="text-white font-medium">{trade.symbol}</span>
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
