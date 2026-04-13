import yfinance as yf
from agents.base_agent import BaseAgent

class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__("Data Agent")

    def run(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            info  = stock.info
            hist  = stock.history(period="6mo")

            # ✅ FIX 5: validar que info no venga vacío
            if not info or info.get("regularMarketPrice") is None:
                raise ValueError(f"No se encontró información para el ticker '{ticker}'. "
                                 "Puede estar mal escrito o delisted.")

            if hist.empty:
                raise ValueError(f"No hay datos históricos de precios para '{ticker}'.")

            # ── 📊 Momentum (sin cambio) ──────────────────────────────────
            momentum = round(
                (hist["Close"].iloc[-1] / hist["Close"].iloc[0]) - 1, 4
            )

            # ── 📉 Volatilidad ANUALIZADA ─────────────────────────────────
            # ✅ FIX 2: multiplicar por √252 para anualizarla
            volatility = round(
                hist["Close"].pct_change().std() * (252 ** 0.5), 4
            )

            # ── 🔢 Debt/Equity normalizado ────────────────────────────────
            # ✅ FIX 3: yfinance lo entrega en % (186.5 → 1.865)
            raw_de = info.get("debtToEquity")
            debt_to_equity = round(raw_de / 100, 4) if raw_de is not None else None

            # ── 📈 Campos para PEGY ───────────────────────────────────────
            # ✅ FIX 1: agregamos eps_growth y dividend_yield
            eps_growth     = info.get("earningsGrowth")
            dividend_yield = info.get("dividendYield")

            ratios = {
                "pe":             info.get("trailingPE"),
                "roe":            info.get("returnOnEquity"),
                "debt_to_equity": debt_to_equity,
                "revenue_growth": info.get("revenueGrowth"),
                "fcf":            info.get("freeCashflow"),
                "momentum":       momentum,
                "volatility":     volatility,
                # Nuevos campos para PEGY
                "eps_growth":     eps_growth,
                "dividend_yield": dividend_yield,
            }

            return {
                "ratios": ratios,
                "financial_health_summary": "Data retrieved successfully"
            }

        # ✅ FIX 4: error específico con mensaje útil para el usuario
        except ValueError as e:
            return {
                "ratios": {},
                "financial_health_summary": f"Error de datos: {str(e)}"
            }
        except Exception as e:
            return {
                "ratios": {},
                "financial_health_summary": f"Error inesperado al procesar '{ticker}': {str(e)}"
            }