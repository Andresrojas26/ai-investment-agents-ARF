from agents.base_agent import BaseAgent

class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("Analysis Agent")

    def run(self, data_result, news_result):

        ratios = data_result["ratios"]
        sentiment = news_result["sentiment_score"]

        score = 0

        # 📊 Fundamentales
        if ratios.get("pe") and ratios["pe"] < 25:
            score += 2
        if ratios.get("roe") and ratios["roe"] > 0.15:
            score += 2
        if ratios.get("debt_to_equity") and ratios["debt_to_equity"] < 1:
            score += 2
        if ratios.get("revenue_growth") and ratios["revenue_growth"] > 0.05:
            score += 2
        if ratios.get("fcf") and ratios["fcf"] > 0:
            score += 2

        # 🚀 Momentum
        if ratios.get("momentum") and ratios["momentum"] > 0:
            score += 2

        # ⚠️ Penalización por volatilidad
        if ratios.get("volatility") and ratios["volatility"] > 0.03:
            score -= 2

        # 📰 Sentimiento (0–10)
        sentiment_score = (sentiment + 1) * 5

        total_score = (score * 0.7) + (sentiment_score * 0.3)

        return {
            "financial_score": score,
            "sentiment_score": sentiment_score,
            "total_score": total_score,
            "volatility": ratios.get("volatility", 0.02)
        }