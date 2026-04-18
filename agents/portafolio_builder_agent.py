import os
import json
import streamlit as st
from groq import Groq
from agents.base_agent import BaseAgent

# ✅ Lee desde Streamlit Secrets (nube) o variable de entorno (local)
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    print("[WARNING] No se encontró GROQ_API_KEY.")

UNIVERSE_BY_RISK = {
    "low": """
        Prioriza: ETFs de dividendos (VYM, SCHD), Consumer Staples (KO, PG, JNJ, CL),
        Utilities (NEE, DUK, SO), REITs estables (O, PLD), Healthcare defensivo (ABT, MDT).
        Evita: tecnología especulativa, small caps, alta volatilidad.
        Beta objetivo del portafolio: < 0.8.
    """,
    "medium": """
        Mezcla: Blue chips tecnológicos (AAPL, MSFT, GOOGL), Healthcare (UNH, LLY),
        Industriales (HON, CAT, DE), Financieros (JPM, V), ETFs diversificados (SPY, QQQ).
        Incluye algo de crecimiento moderado. Beta objetivo: 0.8 - 1.2.
    """,
    "high": """
        Prioriza: Growth tech (NVDA, META, TSLA, PLTR), Small/mid caps con momentum,
        Mercados emergentes (MELI, SE, BABA), Sectores disruptivos (ARKK, SOFI, COIN).
        Acepta alta volatilidad a cambio de mayor retorno esperado. Beta objetivo: > 1.2.
    """
}

HORIZON_CONTEXT = {
    "short":  "horizonte de inversión corto (menos de 1 año), prioriza liquidez y menor drawdown.",
    "medium": "horizonte de inversión medio (1-3 años), balance entre crecimiento y estabilidad.",
    "long":   "horizonte de inversión largo (más de 3 años), puede tolerar volatilidad temporal por mayor retorno.",
}


class PortfolioBuilderAgent(BaseAgent):
    def __init__(self):
        super().__init__("Portfolio Builder Agent")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model  = "llama-3.3-70b-versatile"

    def _call(self, prompt: str, max_tokens: int = 1000) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def select_tickers(self, risk_level: str, capital: float, horizon: str = "long", n_stocks: int = 6) -> dict:
        universe = UNIVERSE_BY_RISK.get(risk_level, UNIVERSE_BY_RISK["medium"])
        hor_ctx  = HORIZON_CONTEXT.get(horizon, HORIZON_CONTEXT["long"])

        prompt = f"""
Eres un portfolio manager profesional con CFA. Tu tarea es construir un portafolio
de acciones diversificado para un inversionista con el siguiente perfil:

- Perfil de riesgo: {risk_level.upper()}
- Capital inicial: ${capital:,.0f} USD
- Horizonte: {hor_ctx}
- Número de posiciones: {n_stocks}

Universo de referencia para este perfil:
{universe}

Instrucciones:
1. Selecciona exactamente {n_stocks} tickers del mercado americano (NYSE/NASDAQ).
2. Diversifica por sector — máximo 2 tickers del mismo sector.
3. Para cada ticker explica en 1-2 oraciones por qué lo incluyes dado el perfil.
4. Indica el sector de cada ticker.

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta.
No incluyas texto adicional, explicaciones ni bloques de markdown.
Solo el JSON puro:
{{
    "tickers": [
        {{
            "ticker": "AAPL",
            "sector": "Technology",
            "rationale": "Empresa de alta calidad con flujo de caja robusto y dividendo creciente."
        }}
    ],
    "portfolio_thesis": "Una oración describiendo la tesis general del portafolio."
}}
"""

        try:
            raw = self._call(prompt, max_tokens=1000)

            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            data    = json.loads(raw)
            tickers = [t["ticker"].upper() for t in data["tickers"]]

            return {
                "tickers":          tickers,
                "ticker_details":   data["tickers"],
                "portfolio_thesis": data.get("portfolio_thesis", ""),
            }

        except json.JSONDecodeError as e:
            print(f"[PortfolioBuilder] Error parseando JSON: {e}")
            raise ValueError(f"El modelo no retornó un JSON válido. Intenta de nuevo. Detalle: {e}")
        except Exception as e:
            print(f"[PortfolioBuilder] Error en select_tickers: {e}")
            raise

    def generate_narrative(
        self,
        reports: list,
        risk_level: str,
        capital: float,
        ticker_details: list,
        bt_result: dict,
        bench_result: dict
    ) -> str:

        summary_lines = []
        for r in reports:
            rec      = r["decision"].get("recommendation", "N/A")
            conf     = r["decision"].get("confidence", 0)
            sent     = r["sentiment"].get("sentiment_score", 0)
            vol      = r.get("analysis", {}).get("volatility", 0) or 0
            beta_raw = r.get("analysis", {}).get("beta")
            beta_str = f"{beta_raw:.2f}" if isinstance(beta_raw, float) else "N/A"

            summary_lines.append(
                f"- {r['ticker']}: {rec} (confianza {conf}), "
                f"sentimiento {sent:.2f}, volatilidad {vol:.2%}, beta {beta_str}"
            )

        rationale_lines = [
            f"- {t['ticker']} ({t['sector']}): {t['rationale']}"
            for t in ticker_details
        ]

        prompt = f"""
Eres un portfolio manager profesional con CFA. Acabas de construir un portafolio
para un cliente con perfil de riesgo {risk_level.upper()} y capital de ${capital:,.0f} USD.

Resultados del análisis cuantitativo:
{chr(10).join(summary_lines)}

Retorno del portafolio (backtest): {bt_result.get('portfolio_return', 0)*100:.2f}%
Sharpe Ratio: {bt_result.get('sharpe_ratio', 0):.2f}
Sortino Ratio: {bt_result.get('sortino_ratio', 0):.2f}
Max Drawdown: {bt_result.get('max_drawdown', 0)*100:.2f}%
VaR 95%: {bt_result.get('var_95', 0)*100:.2f}%
Alpha vs S&P 500: {bench_result.get('alpha', 0)*100:.2f}%
Jensen's Alpha: {bench_result.get('jensens_alpha', 0)*100:.2f}%

Tesis cualitativa por activo:
{chr(10).join(rationale_lines)}

Escribe un análisis narrativo profesional del portafolio en español con estas secciones:
1. Tesis de inversión (2-3 oraciones)
2. Diversificación y cobertura sectorial (2-3 oraciones)
3. Evaluación del riesgo (menciona Sharpe, drawdown y VaR de forma natural)
4. Contexto de mercado y sentimiento (basado en los scores de sentimiento)
5. Recomendación final (1-2 oraciones)

Tono: profesional, directo, sin exageraciones. Máximo 250 palabras.
"""

        try:
            return self._call(prompt, max_tokens=800)
        except Exception as e:
            print(f"[PortfolioBuilder] Error generando narrativa: {e}")
            return "Narrative unavailable — error connecting to Groq."