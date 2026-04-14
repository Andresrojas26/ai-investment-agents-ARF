import pandas as pd
import yfinance as yf
import numpy as np
from agents.base_agent import BaseAgent


def calculate_beta(ticker: str, period: str = "1y") -> float | None:
    """Beta del activo respecto al S&P 500."""
    try:
        stock_hist  = yf.Ticker(ticker).history(period=period)["Close"].pct_change().dropna()
        market_hist = yf.Ticker("^GSPC").history(period=period)["Close"].pct_change().dropna()

        df = pd.concat([stock_hist, market_hist], axis=1).dropna()
        df.columns = ["stock", "market"]

        if df.empty or df["market"].var() == 0:
            return None

        cov     = df.cov().iloc[0, 1]
        var_mkt = df["market"].var()
        return round(cov / var_mkt, 4)
    except Exception:
        return None


class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__("Data Agent")

    def run(self, ticker: str) -> dict:
        try:
            stock = yf.Ticker(ticker)
            info  = stock.info
            hist  = stock.history(period="6mo")

            if not info or info.get("regularMarketPrice") is None:
                raise ValueError(
                    f"No se encontró información para '{ticker}'. "
                    "Puede estar mal escrito o delisted."
                )
            if hist.empty:
                raise ValueError(f"No hay datos históricos de precios para '{ticker}'.")

            # Momentum
            momentum = round(
                (hist["Close"].iloc[-1] / hist["Close"].iloc[0]) - 1, 4
            )

            # Volatilidad anualizada
            volatility = round(
                hist["Close"].pct_change().std() * (252 ** 0.5), 4
            )

            # Debt/Equity normalizado (yfinance lo entrega en %)
            raw_de         = info.get("debtToEquity")
            debt_to_equity = round(raw_de / 100, 4) if raw_de is not None else None

            # ✅ Beta vs S&P 500
            beta = calculate_beta(ticker)

            # Campos para PEGY
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
                "beta":           beta,
                "eps_growth":     eps_growth,
                "dividend_yield": dividend_yield,
            }

            return {
                "ratios":                  ratios,
                "financial_health_summary": "Data retrieved successfully"
            }

        except ValueError as e:
            return {
                "ratios":                  {},
                "financial_health_summary": f"Error de datos: {str(e)}"
            }
        except Exception as e:
            return {
                "ratios":                  {},
                "financial_health_summary": f"Error inesperado al procesar '{ticker}': {str(e)}"
            }