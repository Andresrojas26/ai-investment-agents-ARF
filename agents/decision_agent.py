from agents.base_agent import BaseAgent

class DecisionAgent(BaseAgent):
    def __init__(self):
        super().__init__("Decision Agent")

    def run(self, analysis_result, user_profile):
        score = analysis_result["total_score"]
        risk = user_profile["risk_level"]

        # Ajuste por riesgo
        if risk == "low":
            score -= 1
        elif risk == "high":
            score += 1

        if score >= 8:
            recommendation = "BUY"
            horizon = "LONG"
        elif score >= 5:
            recommendation = "HOLD"
            horizon = "MEDIUM"
        else:
            recommendation = "SELL"
            horizon = "SHORT"

        return {
            "recommendation": recommendation,
            "horizon": horizon,
            "confidence": round(score * 10, 2),
            "adjusted_for_risk": risk
        }