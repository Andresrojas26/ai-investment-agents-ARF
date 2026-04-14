from agents.base_agent import BaseAgent


class DecisionAgent(BaseAgent):
    def __init__(self):
        super().__init__("Decision Agent")

    def run(self, analysis_result, user_profile, portfolio_context=None):
        score = analysis_result["total_score"]
        risk  = user_profile.get("risk_level", "medium")
        beta  = analysis_result.get("beta")

        # ── Ajuste por perfil de riesgo ────────────────────────────────────
        if risk == "low":
            score -= 1.5
            # Perfil conservador: penaliza fuerte activos de alto beta
            if beta is not None and beta > 1.2:
                score -= 1
        elif risk == "high":
            score += 1
            # Perfil agresivo: bonifica activos con alto momentum
            if analysis_result.get("ratios", {}).get("momentum", 0) > 0.10:
                score += 0.5

        # ── Ajuste por contexto de portafolio ─────────────────────────────
        # Si el portafolio ya está sobre-expuesto a este activo, penaliza
        if portfolio_context:
            existing_weight = portfolio_context.get("existing_weight", 0)
            max_allowed     = portfolio_context.get("max_weight", 0.4)
            if existing_weight >= max_allowed:
                score -= 2   # ya no cabe más de este activo

        # ── Thresholds ajustados por riesgo ───────────────────────────────
        thresholds = {
            "low":    {"buy": 8.5, "hold": 6.0},
            "medium": {"buy": 7.5, "hold": 5.0},
            "high":   {"buy": 6.5, "hold": 4.0},
        }
        t = thresholds.get(risk, thresholds["medium"])

        if score >= t["buy"]:
            recommendation = "BUY"
            horizon        = "LONG"
        elif score >= t["hold"]:
            recommendation = "HOLD"
            horizon        = "MEDIUM"
        else:
            recommendation = "SELL"
            horizon        = "SHORT"

        # Confianza: normalizada 0–100
        confidence = round(min(max(score * 10, 0), 100), 2)

        return {
            "recommendation":    recommendation,
            "horizon":           horizon,
            "confidence":        confidence,
            "adjusted_for_risk": risk,
            "score_used":        round(score, 2),
        }