import numpy as np
import pandas as pd
import yfinance as yf
from agents.base_agent import BaseAgent


def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Value at Risk histórico."""
    return round(float(np.percentile(returns, (1 - confidence) * 100)), 6)


def calculate_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """Conditional VaR (Expected Shortfall) — promedio de pérdidas más allá del VaR."""
    var = calculate_var(returns, confidence)
    tail = returns[returns <= var]
    return round(float(tail.mean()), 6) if not tail.empty else var


def calculate_max_drawdown(returns: pd.Series) -> float:
    """Máxima caída de pico a valle."""
    cumulative  = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown    = (cumulative - rolling_max) / rolling_max
    return round(float(drawdown.min()), 6)


def calculate_sortino(returns: pd.Series, risk_free_rate: float = 0.05) -> float:
    """Sortino ratio — penaliza solo la volatilidad negativa."""
    daily_rf      = risk_free_rate / 252
    excess        = returns - daily_rf
    downside      = excess[excess < 0].std() * np.sqrt(252)
    annual_return = returns.mean() * 252
    if downside == 0:
        return 0.0
    return round((annual_return - risk_free_rate) / downside, 4)


class BacktestingAgent(BaseAgent):
    def __init__(self):
        super().__init__("Backtesting Agent")

    def run(self, portfolio: list, period: str = "6mo") -> dict:
        returns_list   = []
        stock_results  = []
        portfolio_beta = 0.0
        total_weight   = 0.0

        for stock in portfolio:
            ticker = stock["ticker"]
            weight = stock["weight"]
            beta   = stock.get("beta") or 1.0   # beta del portafolio ponderado

            data = yf.Ticker(ticker).history(period=period)
            if data.empty:
                continue

            returns          = data["Close"].pct_change().dropna()
            weighted_returns = returns * weight
            returns_list.append(weighted_returns)

            total_return = round(
                float((data["Close"].iloc[-1] / data["Close"].iloc[0]) - 1), 6
            )

            stock_results.append({
                "ticker": ticker,
                "return": total_return,
                "weight": weight,
            })

            # Beta ponderado del portafolio
            portfolio_beta += beta * weight
            total_weight   += weight

        if not returns_list:
            return {
                "stocks":           [],
                "portfolio_return": 0,
                "volatility":       0,
                "sharpe_ratio":     0,
                "sortino_ratio":    0,
                "max_drawdown":     0,
                "var_95":           0,
                "cvar_95":          0,
                "portfolio_beta":   1.0,
            }

        # Serie de retornos del portafolio completo
        portfolio_series = sum(returns_list)

        total_return = round(float(portfolio_series.sum()), 6)
        volatility   = round(float(portfolio_series.std() * np.sqrt(252)), 6)

        risk_free_daily = 0.05 / 252
        sharpe = round(
            float((portfolio_series.mean() - risk_free_daily) / portfolio_series.std() * np.sqrt(252)), 4
        ) if portfolio_series.std() != 0 else 0

        # ✅ Nuevas métricas
        sortino      = calculate_sortino(portfolio_series)
        max_drawdown = calculate_max_drawdown(portfolio_series)
        var_95       = calculate_var(portfolio_series, confidence=0.95)
        cvar_95      = calculate_cvar(portfolio_series, confidence=0.95)

        beta_normalized = round(portfolio_beta / total_weight, 4) if total_weight > 0 else 1.0

        return {
            "stocks":           stock_results,
            "portfolio_return": total_return,
            "volatility":       volatility,
            "sharpe_ratio":     sharpe,
            "sortino_ratio":    sortino,       # ✅
            "max_drawdown":     max_drawdown,  # ✅
            "var_95":           var_95,        # ✅
            "cvar_95":          cvar_95,       # ✅
            "portfolio_beta":   beta_normalized,
        }