"""
AI Trade Analyzer - Uses Claude to analyze trading patterns from screenshots
"""

import os
import base64
import anthropic
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TradeForAnalysis:
    """Trade data for AI analysis"""
    id: int
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float]
    pnl: Optional[float]
    pnl_percent: Optional[float]
    strategy: Optional[str]
    timeframe: Optional[str]
    confidence_level: Optional[int]
    image_url: Optional[str]  # Base64 entry image
    exit_image_url: Optional[str]  # Base64 exit image
    notes: Optional[str]
    exit_notes: Optional[str]


class AITradeAnalyzer:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def _prepare_image_content(self, base64_data: str) -> dict:
        """Prepare image for Claude API"""
        # Remove data URL prefix if present
        if base64_data.startswith("data:"):
            # Extract media type and base64 data
            parts = base64_data.split(",", 1)
            if len(parts) == 2:
                media_type_part = parts[0]  # e.g., "data:image/png;base64"
                base64_data = parts[1]
                # Extract media type
                media_type = media_type_part.split(":")[1].split(";")[0]
            else:
                media_type = "image/png"
        else:
            media_type = "image/png"

        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64_data,
            }
        }

    async def analyze_trades(self, trades: List[TradeForAnalysis], month: int, year: int) -> dict:
        """Analyze trades using Claude vision"""

        if not trades:
            return {
                "success": False,
                "error": "No hay trades para analizar en este período"
            }

        # Separate winning and losing trades
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl < 0]

        # Prepare content with images
        content = []

        # Add text context
        trades_summary = f"""
Análisis de Trading - {month}/{year}

Total de trades cerrados: {len(trades)}
Trades ganadores: {len(winning_trades)}
Trades perdedores: {len(losing_trades)}
Win rate: {(len(winning_trades) / len(trades) * 100):.1f}%

Detalles de cada trade:
"""

        for i, trade in enumerate(trades[:15], 1):  # Limit to 15 trades for token management
            result = "✅ GANADOR" if trade.pnl and trade.pnl > 0 else "❌ PERDEDOR"
            trades_summary += f"""
Trade #{i}: {trade.symbol} ({trade.side.upper()})
- Resultado: {result}
- PnL: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)
- Estrategia: {trade.strategy or 'No especificada'}
- Timeframe: {trade.timeframe or 'No especificado'}
- Confianza: {trade.confidence_level or 'No especificada'}/5
- Entry: ${trade.entry_price:.4f} → Exit: ${trade.exit_price:.4f}
- Notas entrada: {trade.notes or 'Sin notas'}
- Notas salida: {trade.exit_notes or 'Sin notas'}
"""

        content.append({"type": "text", "text": trades_summary})

        # Add images (limit to avoid token limits)
        image_count = 0
        max_images = 10  # Claude can handle many images but we limit for cost

        for trade in trades[:15]:
            if image_count >= max_images:
                break

            if trade.image_url:
                try:
                    content.append(self._prepare_image_content(trade.image_url))
                    content.append({
                        "type": "text",
                        "text": f"[Imagen entrada - Trade {trade.symbol} {'✅' if trade.pnl and trade.pnl > 0 else '❌'}]"
                    })
                    image_count += 1
                except Exception:
                    pass  # Skip invalid images

            if trade.exit_image_url and image_count < max_images:
                try:
                    content.append(self._prepare_image_content(trade.exit_image_url))
                    content.append({
                        "type": "text",
                        "text": f"[Imagen salida - Trade {trade.symbol}]"
                    })
                    image_count += 1
                except Exception:
                    pass

        # Add the analysis prompt
        content.append({
            "type": "text",
            "text": """
Analiza estos trades de trading y sus screenshots de charts.

Por favor analiza:

1. **Patrones Ganadores**: ¿Qué características visuales tienen en común los trades ganadores?
   - Estructura de precio, niveles, formaciones de velas
   - Contexto del mercado (tendencia, rango)

2. **Patrones Perdedores**: ¿Qué errores o señales de alerta se ven en los trades perdedores?
   - ¿Entraron contra tendencia?
   - ¿Ignoraron niveles importantes?

3. **Correlación Confianza-Resultado**: ¿Los trades con alta confianza tuvieron mejor resultado?

4. **Setups a Repetir**: ¿Qué setups específicos funcionaron mejor?

5. **Setups a Evitar**: ¿Qué tipo de entradas deberían evitarse?

6. **Recomendaciones**: 3 consejos concretos para mejorar el trading basándote en este análisis.

Responde en español, de forma concisa y actionable. Usa emojis para hacer el análisis más visual.
"""
        })

        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": content}
                ]
            )

            analysis_text = response.content[0].text

            return {
                "success": True,
                "month": month,
                "year": year,
                "total_trades": len(trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": (len(winning_trades) / len(trades) * 100) if trades else 0,
                "images_analyzed": image_count,
                "analysis": analysis_text,
            }

        except anthropic.APIError as e:
            return {
                "success": False,
                "error": f"Error de API de Claude: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}"
            }
