from agents.base_agent import BaseAgent

class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("Analysis Agent")

    def run(self, data_result, news_result):

        ratios    = data_result["ratios"]
        sentiment = news_result["sentiment_score"]

        score     = 0
        max_score = 0  # ✅ FIX 2: llevamos la cuenta del máximo para normalizar

        # ── 📊 FUNDAMENTALES ─────────────────────────────────────────────────

        max_score += 2
        # ✅ FIX 1: is not None en vez de truthy check
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

        # ── 🚀 MOMENTUM ──────────────────────────────────────────────────────

        max_score += 2
        # ✅ FIX 6: umbral mínimo significativo (>2%) en vez de cualquier positivo
        if ratios.get("momentum") is not None and ratios["momentum"] > 0.02:
            score += 2

        # ── ⚠️ VOLATILIDAD ───────────────────────────────────────────────────

        max_score += 2
        # ✅ FIX 3: umbral ajustado a 0.30 (30% anualizado) — más realista
        if ratios.get("volatility") is not None and ratios["volatility"] > 0.30:
            score -= 2

        # ── 🔢 PEGY RATIO ────────────────────────────────────────────────────
        # PEGY = P/E ÷ (crecimiento EPS % + dividend yield %)
        # Usa eps_growth si está disponible, sino revenue_growth como proxy

        pegy = None
        pe            = ratios.get("pe")
        eps_growth    = ratios.get("eps_growth") or ratios.get("revenue_growth")
        dividend_yield = ratios.get("dividend_yield", 0) or 0

        if pe is not None and eps_growth is not None:
            # Convertir a porcentaje si vienen en formato decimal (ej: 0.12 → 12)
            eps_pct  = eps_growth * 100  if abs(eps_growth)  <= 1 else eps_growth
            div_pct  = dividend_yield * 100 if abs(dividend_yield) <= 1 else dividend_yield
            divisor  = eps_pct + div_pct

            if divisor > 0:
                pegy = round(pe / divisor, 2)

                max_score += 2
                if pegy < 1:
                    score += 2   # subvalorada según PEGY ✅
                elif pegy > 2:
                    score -= 1   # sobrevalorada según PEGY ⚠️

        # ── 📰 SENTIMIENTO ────────────────────────────────────────────────────

        # Convierte score de sentimiento de [-1, 1] a [0, 10]
        sentiment_score = round((sentiment + 1) * 5, 2)

        # ── 🧮 SCORE FINAL NORMALIZADO ────────────────────────────────────────
        # ✅ FIX 2: normalizamos financial_score a [0, 10] antes de combinar
        financial_score_raw        = max(score, 0)
        financial_score_normalized = round((financial_score_raw / max_score) * 10, 2) if max_score > 0 else 0

        total_score = round(
            (financial_score_normalized * 0.7) + (sentiment_score * 0.3), 2
        )

        # ✅ FIX 4: retornamos ratios para que agentes posteriores los usen
        return {
            "financial_score": financial_score_normalized,
            "financial_score_raw": score,
            "sentiment_score": sentiment_score,
            "total_score": total_score,
            "pegy": pegy,                              # None si no hay datos suficientes
            "volatility": ratios.get("volatility", 0),
            "ratios": ratios                           # ✅ disponible para agentes posteriores
        }