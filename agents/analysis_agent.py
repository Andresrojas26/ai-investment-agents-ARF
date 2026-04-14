from agents.base_agent import BaseAgent

RISK_PROFILES = {
    "low":    {"max_weight": 0.20, "hold_penalty": 0.40, "vol_power": 2.0, "min_positions": 3, "floor_weight": 0.05},
    "medium": {"max_weight": 0.35, "hold_penalty": 0.70, "vol_power": 1.0, "min_positions": 2, "floor_weight": 0.03},
    "high":   {"max_weight": 0.50, "hold_penalty": 0.90, "vol_power": 0.5, "min_positions": 1, "floor_weight": 0.0},
}


class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("Analysis Agent")

    def run(self, data_result, news_result):
        ratios    = data_result.get("ratios", {})
        sentiment = news_result.get("sentiment_score", 0)

        score     = 0
        max_score = 0

        # ── Fundamentales ──────────────────────────────────────────────────
        max_score += 2
        if ratios.get("pe") is not None and ratios["pe"] < 25:
            score += 2

        max_score += 2
        if ratios.get("roe") is not None and ratios["roe"] > 0.15:
            score += 2

        max_score += 2
        if ratios.get("debt_to_equity") is not None and ratios["debt_to_equity"] < 1:
            score += 2

        max_score += 2
        if ratios.get("revenue_growth") is not None and ratios["revenue_growth"] > 0.05:
            score += 2

        max_score += 2
        if ratios.get("fcf") is not None and ratios["fcf"] > 0:
            score += 2

        # ── Momentum ───────────────────────────────────────────────────────
        max_score += 2
        if ratios.get("momentum") is not None and ratios["momentum"] > 0.02:
            score += 2

        # ── Beta ───────────────────────────────────────────────────────────
        # Beta < 1 → menos riesgo sistémico → bonificación
        # Beta > 1.5 → riesgo alto → penalización
        max_score += 2
        beta = ratios.get("beta")
        if beta is not None:
            if beta < 1.0:
                score += 2
            elif beta <= 1.5:
                score += 1
            else:
                score -= 1

        # ── Volatilidad ────────────────────────────────────────────────────
        max_score += 2
        if ratios.get("volatility") is not None and ratios["volatility"] > 0.30:
            score -= 2

        # ── PEGY ───────────────────────────────────────────────────────────
        pegy       = None
        pe         = ratios.get("pe")
        eps_growth = ratios.get("eps_growth") or ratios.get("revenue_growth")
        div_yield  = ratios.get("dividend_yield", 0) or 0

        if pe is not None and eps_growth is not None:
            eps_pct = eps_growth * 100 if abs(eps_growth) <= 1 else eps_growth
            div_pct = div_yield  * 100 if abs(div_yield)  <= 1 else div_yield
            divisor = eps_pct + div_pct

            if divisor > 0:
                pegy = round(pe / divisor, 2)
                max_score += 2
                if pegy < 1:
                    score += 2
                elif pegy > 2:
                    score -= 1

        # ── Sentimiento ────────────────────────────────────────────────────
        sentiment_score = round((sentiment + 1) * 5, 2)

        # ── Score final normalizado ────────────────────────────────────────
        financial_score_raw        = max(score, 0)
        financial_score_normalized = round(
            (financial_score_raw / max_score) * 10, 2
        ) if max_score > 0 else 0

        total_score = round(
            (financial_score_normalized * 0.7) + (sentiment_score * 0.3), 2
        )

        return {
            "financial_score":     financial_score_normalized,
            "financial_score_raw": score,
            "sentiment_score":     sentiment_score,
            "total_score":         total_score,
            "pegy":                pegy,
            "beta":                beta,
            "volatility":          ratios.get("volatility", 0),
            "ratios":              ratios,
        }