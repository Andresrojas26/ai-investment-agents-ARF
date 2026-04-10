import yfinance as yf
from agents.base_agent import BaseAgent

class BenchmarkAgent(BaseAgent):
    def __init__(self):
        super().__init__("Benchmark Agent")

    def run(self, portfolio_return, period="6mo"):

        data = yf.Ticker("^GSPC").history(period=period)

        if data.empty:
            return {"error": "No data"}

        start = data["Close"].iloc[0]
        end = data["Close"].iloc[-1]

        benchmark_return = (end - start) / start
        alpha = portfolio_return - benchmark_return

        return {
            "benchmark_return": benchmark_return,
            "portfolio_return": portfolio_return,
            "alpha": alpha
        }