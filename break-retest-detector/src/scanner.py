"""
Scanner de Break & Retest
Monitorea múltiples símbolos y timeframes
"""

import asyncio
from typing import List, Dict, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

from .detector import BreakRetestDetector, Signal, create_detector
from .binance_client import get_binance_client, close_client


@dataclass
class ScanConfig:
    """Configuración del scanner"""
    symbols: List[str]
    timeframes: List[str]
    sensitivity: str = "medium"
    scan_interval_seconds: int = 300  # 5 minutos por defecto


class Scanner:
    """
    Scanner de patrones Break & Retest
    
    Escanea múltiples símbolos y timeframes en busca de retesteos.
    """
    
    def __init__(
        self,
        config: ScanConfig,
        on_signal: Optional[Callable[[Signal], None]] = None
    ):
        self.config = config
        self.on_signal = on_signal
        self.detector = create_detector(config.sensitivity)
        self.binance = get_binance_client()
        self.running = False
        self.last_scan: Optional[datetime] = None
        self.signals_found: List[Signal] = []
    
    async def scan_symbol(
        self,
        symbol: str,
        timeframe: str
    ) -> List[Signal]:
        """Escanea un símbolo/timeframe específico"""
        try:
            df = await self.binance.get_klines(symbol, timeframe, limit=500)
            signals = self.detector.detect(df, symbol, timeframe)
            return signals
        except Exception as e:
            print(f"Error scanning {symbol} {timeframe}: {e}")
            return []
    
    async def scan_all(self) -> List[Signal]:
        """Escanea todos los símbolos y timeframes configurados"""
        all_signals = []
        
        print(f"\n{'='*50}")
        print(f"🔍 Escaneando {len(self.config.symbols)} símbolos...")
        print(f"   Timeframes: {', '.join(self.config.timeframes)}")
        print(f"   Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        for symbol in self.config.symbols:
            for timeframe in self.config.timeframes:
                signals = await self.scan_symbol(symbol, timeframe)
                
                for signal in signals:
                    all_signals.append(signal)
                    print(signal.message)
                    print("-" * 40)
                    
                    if self.on_signal:
                        self.on_signal(signal)
                
                # Pequeña pausa para no saturar la API
                await asyncio.sleep(0.1)
        
        self.last_scan = datetime.now()
        self.signals_found = all_signals
        
        if not all_signals:
            print("✓ Scan completado. No se encontraron señales de retest.")
        else:
            print(f"\n🎯 Se encontraron {len(all_signals)} señales!")
        
        return all_signals
    
    async def run_continuous(self):
        """Ejecuta el scanner continuamente"""
        self.running = True
        
        print(f"""
╔══════════════════════════════════════════════════════╗
║       BREAK & RETEST SCANNER - INICIADO              ║
╠══════════════════════════════════════════════════════╣
║  Símbolos: {len(self.config.symbols):3d}                                     ║
║  Timeframes: {', '.join(self.config.timeframes):40s} ║
║  Intervalo: cada {self.config.scan_interval_seconds} segundos                       ║
║  Sensibilidad: {self.config.sensitivity:40s} ║
╚══════════════════════════════════════════════════════╝
        """)
        
        while self.running:
            try:
                await self.scan_all()
                
                print(f"\n⏰ Próximo scan en {self.config.scan_interval_seconds} segundos...")
                print(f"   (Presiona Ctrl+C para detener)\n")
                
                await asyncio.sleep(self.config.scan_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error en scan: {e}")
                await asyncio.sleep(60)
        
        await close_client()
        print("\n🛑 Scanner detenido.")
    
    def stop(self):
        """Detiene el scanner"""
        self.running = False


async def quick_scan(
    symbols: List[str],
    timeframes: List[str] = ["1h", "4h"],
    sensitivity: str = "medium"
) -> List[Signal]:
    """
    Realiza un scan rápido (una sola vez)
    
    Args:
        symbols: Lista de símbolos (ej: ["BTCUSDT", "ETHUSDT"])
        timeframes: Lista de timeframes
        sensitivity: "low", "medium", "high"
    
    Returns:
        Lista de señales encontradas
    """
    config = ScanConfig(
        symbols=symbols,
        timeframes=timeframes,
        sensitivity=sensitivity
    )
    
    scanner = Scanner(config)
    signals = await scanner.scan_all()
    await close_client()
    
    return signals


# Símbolos populares para escanear
POPULAR_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT", "APTUSDT"
]

TOP_10_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT"
]
