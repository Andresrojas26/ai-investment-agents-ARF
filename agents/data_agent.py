import yfinance as yf
from agents.base_agent import BaseAgent

class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__("Data Agent")

    def run(self, ticker):
        try:
            stock = yf.Ticker(ticker)

            info = stock.info
            hist = stock.history(period="6mo")

            if hist.empty:
                raise ValueError("No price data")

            # 📊 Momentum
            momentum = (hist["Close"].iloc[-1] / hist["Close"].iloc[0]) - 1

            # 📉 Volatilidad
            volatility = hist["Close"].pct_change().std()

            ratios = {
                "pe": info.get("trailingPE"),
                "roe": info.get("returnOnEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "fcf": info.get("freeCashflow"),
                "momentum": momentum,
                "volatility": volatility
            }

            return {
                "ratios": ratios,
                "financial_health_summary": "Data retrieved successfully"
            }

        except Exception as e:
            return {
                "ratios": {},
                "financial_health_summary": f"Error: {str(e)}"
            }