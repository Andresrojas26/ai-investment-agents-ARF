import pandas as pd
import yfinance as yf
from agents.base_agent import BaseAgent


RISK_PROFILES = {
    "low":    {"max_weight": 0.20, "hold_penalty": 0.40, "vol_power": 2.0, "min_positions": 3, "floor_weight": 0.05},
    "medium": {"max_weight": 0.35, "hold_penalty": 0.70, "vol_power": 1.0, "min_positions": 2, "floor_weight": 0.03},
    "high":   {"max_weight": 0.50, "hold_penalty": 0.90, "vol_power": 0.5, "min_positions": 1, "floor_weight": 0.0},
}

CORRELATION_THRESHOLD = 0.80   # si dos activos tienen correlación > 0.8, reducimos el de menor score


def get_correlation_matrix(tickers: list, period: str = "6mo") -> pd.DataFrame | None:
    """Descarga retornos y calcula matriz de correlación entre activos."""
    try:
        data = {}
        for ticker in tickers:
            hist = yf.Ticker(ticker).history(period=period)["Close"]
            if not hist.empty:
                data[ticker] = hist.pct_change().dropna()
        if len(data) < 2:
            return None
        df = pd.DataFrame(data).dropna()
        return df.corr()
    except Exception:
        return None


class PortfolioAgent(BaseAgent):
    def __init__(self):
        super().__init__("Portfolio Agent")

    def run(self, reports: list, capital: float, risk_level: str = "medium") -> dict:
        profile = RISK_PROFILES.get(risk_level, RISK_PROFILES["medium"])

        # ── PASO 1: Filtrar y puntuar candidatos ──────────────────────────
        candidates = []
        for r in reports:
            rec        = r["decision"]["recommendation"]
            confidence = r["decision"].get("confidence", 0)
            volatility = r["analysis"].get("volatility", 0.02)
            beta       = r["analysis"].get("beta") or 1.0

            if rec not in ["BUY", "HOLD", "COMPRAR", "MANTENER"]:
                continue

            vol_safe = max(volatility, 0.01)
            score    = confidence / (vol_safe ** profile["vol_power"])

            if rec in ["HOLD", "MANTENER"]:
                score *= profile["hold_penalty"]

            candidates.append({
                "ticker":     r["ticker"],
                "score":      score,
                "rec":        rec,
                "volatility": volatility,
                "confidence": confidence,
                "beta":       beta,
            })

        if not candidates:
            return {
                "portfolio":  [],
                "message":    "No opportunities found for current risk profile.",
                "risk_level": risk_level,
            }

        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

        # ── PASO 2: Penalización por alta correlación ─────────────────────
        tickers_list = [c["ticker"] for c in candidates]
        corr_matrix  = get_correlation_matrix(tickers_list)

        if corr_matrix is not None:
            penalized = set()
            for i in range(len(candidates)):
                for j in range(i + 1, len(candidates)):
                    t1 = candidates[i]["ticker"]
                    t2 = candidates[j]["ticker"]
                    if t1 in corr_matrix.columns and t2 in corr_matrix.columns:
                        corr = abs(corr_matrix.loc[t1, t2])
                        if corr > CORRELATION_THRESHOLD:
                            # Penalizar el de menor score (índice j, ya ordenado desc)
                            penalized.add(t2)

            for c in candidates:
                if c["ticker"] in penalized:
                    c["score"] *= 0.6   # reduce su influencia en el portafolio

            # Reordenar tras penalización
            candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

        # ── PASO 3: Calcular pesos base ───────────────────────────────────
        total_score = sum(c["score"] for c in candidates)
        for c in candidates:
            c["weight"] = c["score"] / total_score if total_score > 0 else 1 / len(candidates)

        # ── PASO 4: Aplicar techo (max_weight) con redistribución ─────────
        max_w = profile["max_weight"]
        for _ in range(10):
            capped = [c for c in candidates if c["weight"] > max_w]
            free   = [c for c in candidates if c["weight"] <= max_w]

            if not capped:
                break

            excess         = sum(c["weight"] - max_w for c in capped)
            free_score_sum = sum(c["score"] for c in free)

            for c in capped:
                c["weight"] = max_w

            if free_score_sum == 0:
                break

            for c in free:
                c["weight"] += excess * (c["score"] / free_score_sum)

        # ── PASO 5: Aplicar piso mínimo ───────────────────────────────────
        floor = profile["floor_weight"]
        if floor > 0:
            for c in candidates:
                if c["weight"] < floor:
                    c["weight"] = floor
            total_w = sum(c["weight"] for c in candidates)
            for c in candidates:
                c["weight"] = c["weight"] / total_w

        # ── PASO 6: Construir portafolio final ────────────────────────────
        portfolio = sorted([
            {
                "ticker":     c["ticker"],
                "weight":     round(c["weight"], 4),
                "allocation": round(c["weight"] * capital, 2),
                "rec":        c["rec"],
                "volatility": round(c["volatility"], 4),
                "confidence": c["confidence"],
                "beta":       c["beta"],
            }
            for c in candidates
        ], key=lambda x: x["weight"], reverse=True)

        return {
            "portfolio":      portfolio,
            "total_invested": capital,
            "risk_level":     risk_level,
            "num_positions":  len(portfolio),
            "message":        f"Portfolio optimized for '{risk_level}' risk profile.",
        }