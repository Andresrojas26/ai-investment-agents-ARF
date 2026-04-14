import yfinance as yf
from agents.base_agent import BaseAgent


def calculate_jensens_alpha(
    portfolio_return: float,
    beta: float,
    benchmark_return: float,
    risk_free_rate: float = 0.05
) -> float:
    """
    Jensen's Alpha = Rp - [Rf + β(Rm - Rf)]
    Mide si el portafolio genera retorno superior al esperado dado su riesgo sistemático.
    """
    expected_return = risk_free_rate + beta * (benchmark_return - risk_free_rate)
    return round(portfolio_return - expected_return, 6)


class BenchmarkAgent(BaseAgent):
    def __init__(self):
        super().__init__("Benchmark Agent")

    def run(self, portfolio_return: float, portfolio_beta: float = 1.0, period: str = "6mo") -> dict:
        data = yf.Ticker("^GSPC").history(period=period)

        if data.empty:
            return {"error": "No benchmark data available"}

        benchmark_return = round(
            float((data["Close"].iloc[-1] / data["Close"].iloc[0]) - 1), 6
        )

        alpha = round(portfolio_return - benchmark_return, 6)

        # ✅ Jensen's Alpha — más riguroso que el alpha simple
        jensens_alpha = calculate_jensens_alpha(
            portfolio_return=portfolio_return,
            beta=portfolio_beta,
            benchmark_return=benchmark_return,
            risk_free_rate=0.05
        )

        return {
            "benchmark_return": benchmark_return,
            "portfolio_return": portfolio_return,
            "alpha":            alpha,
            "jensens_alpha":    jensens_alpha,  # ✅
            "portfolio_beta":   portfolio_beta,
        }