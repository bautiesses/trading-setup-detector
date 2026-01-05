#!/usr/bin/env python3
"""
Break & Retest Scanner - CLI
Uso: python run.py [--symbols BTCUSDT,ETHUSDT] [--timeframes 1h,4h] [--continuous]
"""

import asyncio
import argparse
import sys

from src.scanner import Scanner, ScanConfig, quick_scan, TOP_10_SYMBOLS, POPULAR_SYMBOLS


def print_banner():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ██████╗ ██████╗ ███████╗ █████╗ ██╗  ██╗               ║
    ║   ██╔══██╗██╔══██╗██╔════╝██╔══██╗██║ ██╔╝               ║
    ║   ██████╔╝██████╔╝█████╗  ███████║█████╔╝                ║
    ║   ██╔══██╗██╔══██╗██╔══╝  ██╔══██║██╔═██╗                ║
    ║   ██████╔╝██║  ██║███████╗██║  ██║██║  ██╗               ║
    ║   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝               ║
    ║                                                           ║
    ║   ██████╗ ███████╗████████╗███████╗███████╗████████╗     ║
    ║   ██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝     ║
    ║   ██████╔╝█████╗     ██║   █████╗  ███████╗   ██║        ║
    ║   ██╔══██╗██╔══╝     ██║   ██╔══╝  ╚════██║   ██║        ║
    ║   ██║  ██║███████╗   ██║   ███████╗███████║   ██║        ║
    ║   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚══════╝   ╚═╝        ║
    ║                                                           ║
    ║              DETECTOR DE PATRONES - v1.0                  ║
    ║                   100% GRATIS                             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


async def main():
    parser = argparse.ArgumentParser(
        description="Break & Retest Pattern Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run.py                           # Scan rápido de top 10 cryptos
  python run.py --symbols BTCUSDT,ETHUSDT # Solo BTC y ETH
  python run.py --timeframes 15m,1h,4h    # Múltiples timeframes
  python run.py --continuous              # Modo continuo (cada 5 min)
  python run.py --sensitivity high        # Más señales (menos filtrado)
        """
    )
    
    parser.add_argument(
        "--symbols", "-s",
        type=str,
        default=None,
        help="Símbolos separados por coma (ej: BTCUSDT,ETHUSDT). Default: Top 10"
    )
    
    parser.add_argument(
        "--timeframes", "-t",
        type=str,
        default="1h,4h",
        help="Timeframes separados por coma (ej: 15m,1h,4h). Default: 1h,4h"
    )
    
    parser.add_argument(
        "--sensitivity", "-e",
        type=str,
        choices=["low", "medium", "high"],
        default="medium",
        help="Sensibilidad del detector. Default: medium"
    )
    
    parser.add_argument(
        "--continuous", "-c",
        action="store_true",
        help="Ejecutar continuamente (cada 5 minutos)"
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=300,
        help="Intervalo entre scans en segundos (solo con --continuous). Default: 300"
    )
    
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Escanear todos los símbolos populares (15 cryptos)"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Determinar símbolos
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
    elif args.all:
        symbols = POPULAR_SYMBOLS
    else:
        symbols = TOP_10_SYMBOLS
    
    # Determinar timeframes
    timeframes = [t.strip() for t in args.timeframes.split(",")]
    
    print(f"📊 Símbolos: {', '.join(symbols)}")
    print(f"⏱️  Timeframes: {', '.join(timeframes)}")
    print(f"🎚️  Sensibilidad: {args.sensitivity}")
    print()
    
    if args.continuous:
        # Modo continuo
        config = ScanConfig(
            symbols=symbols,
            timeframes=timeframes,
            sensitivity=args.sensitivity,
            scan_interval_seconds=args.interval
        )
        
        scanner = Scanner(config)
        
        try:
            await scanner.run_continuous()
        except KeyboardInterrupt:
            scanner.stop()
            print("\n👋 Scanner detenido por el usuario.")
    else:
        # Scan único
        signals = await quick_scan(
            symbols=symbols,
            timeframes=timeframes,
            sensitivity=args.sensitivity
        )
        
        if signals:
            print(f"\n{'='*50}")
            print(f"📈 RESUMEN: {len(signals)} señales encontradas")
            print(f"{'='*50}")
            
            bullish = [s for s in signals if "BULLISH" in s.pattern_type.value]
            bearish = [s for s in signals if "BEARISH" in s.pattern_type.value]
            
            print(f"   🟢 Bullish (COMPRA): {len(bullish)}")
            print(f"   🔴 Bearish (VENTA): {len(bearish)}")
        else:
            print("\n✅ Scan completado. No hay señales de retest en este momento.")
            print("   Esto es normal - los retests no ocurren constantemente.")
            print("   Ejecuta con --continuous para monitorear continuamente.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Hasta luego!")
        sys.exit(0)
