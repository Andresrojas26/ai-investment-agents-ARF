import yfinance as yf
import numpy as np
from agents.base_agent import BaseAgent

class BacktestingAgent(BaseAgent):
    def __init__(self):
        super().__init__("Backtesting Agent")

    def run(self, portfolio, period="6mo"):

        returns_list = []
        stock_results = []

        for stock in portfolio:
            ticker = stock["ticker"]
            weight = stock["weight"]

            data = yf.Ticker(ticker).history(period=period)

            if data.empty:
                continue

            returns = data["Close"].pct_change().dropna()
            weighted_returns = returns * weight

            returns_list.append(weighted_returns)

            total_return = (data["Close"].iloc[-1] / data["Close"].iloc[0]) - 1

            stock_results.append({
                "ticker": ticker,
                "return": total_return
            })

        portfolio_series = sum(returns_list)

        total_return = portfolio_series.sum()
        volatility = portfolio_series.std()

        risk_free_rate = 0.02 / 252

        sharpe = (portfolio_series.mean() - risk_free_rate) / volatility

        return {
            "stocks": stock_results,
            "portfolio_return": total_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe
        }