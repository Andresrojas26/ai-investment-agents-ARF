from agents.base_agent import BaseAgent

class PortfolioAgent(BaseAgent):
    def __init__(self):
        super().__init__("Portfolio Agent")

    def run(self, reports, capital):

        selected = []

        for r in reports:
            rec = r["decision"]["recommendation"]

            if rec in ["BUY", "HOLD"]:
                confidence = r["decision"]["confidence"]
                volatility = r["analysis"].get("volatility", 0.02)

                # 🔥 Risk-adjusted score
                score = confidence / max(volatility, 0.01)

                if rec == "HOLD":
                    score *= 0.7

                selected.append({
                    "ticker": r["ticker"],
                    "score": score
                })

        if not selected:
            return {"portfolio": [], "message": "No opportunities"}

        total_score = sum(s["score"] for s in selected)

        portfolio = []

        for s in selected:
            weight = s["score"] / total_score

            # 🔒 limitar concentración
            weight = min(weight, 0.4)

            allocation = weight * capital

            portfolio.append({
                "ticker": s["ticker"],
                "weight": round(weight, 2),
                "allocation": round(allocation, 2)
            })

        return {
            "portfolio": portfolio,
            "total_invested": capital
        }