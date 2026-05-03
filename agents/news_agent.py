import os
import json
import streamlit as st
from groq import Groq
from agents.base_agent import BaseAgent
from tools.news_fetcher import get_news

# ✅ Lee desde Streamlit Secrets o variable de entorno
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Categorías de eventos financieros que Groq va a identificar
EVENT_CATEGORIES = [
    "earnings",        # resultados financieros
    "investment",      # nuevas inversiones o expansión
    "product",         # lanzamiento de producto o servicio
    "regulation",      # regulación o problemas legales
    "leadership",      # cambios en directivos
    "partnership",     # alianzas o adquisiciones
    "loss",            # pérdidas o problemas financieros
    "market",          # movimiento de mercado general
    "macro",           # contexto macroeconómico
    "other",           # otro
]


class NewsAgent(BaseAgent):
    def __init__(self):
        super().__init__("News Agent")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model  = "llama-3.3-70b-versatile"

    def analyze_with_groq(self, ticker: str, company_name: str, articles: list) -> list:
        """
        Envía todos los artículos a Groq en una sola llamada.
        Groq analiza cada uno como analista financiero y retorna:
        - sentiment: positive / negative / neutral
        - score: -1.0 a 1.0
        - category: tipo de evento
        - insight: explicación breve del impacto para inversores
        """
        if not articles:
            return []

        # Construir el contexto de artículos para el prompt
        articles_text = ""
        for i, art in enumerate(articles):
            articles_text += f"""
Article {i+1}:
Title: {art['title']}
Description: {art['description']}
Date: {art['publishedAt'][:10] if art['publishedAt'] else 'Unknown'}
---"""

        prompt = f"""You are a senior financial analyst specialized in equity research.
Analyze the following news articles about {company_name} ({ticker}) from the perspective of a stock investor.

{articles_text}

For each article, provide a financial analysis. You must respond ONLY with a valid JSON array, no markdown, no extra text:
[
  {{
    "index": 0,
    "sentiment": "positive",
    "score": 0.7,
    "category": "earnings",
    "insight": "Brief explanation of why this matters for investors (1-2 sentences in English)."
  }}
]

Rules:
- sentiment must be exactly: "positive", "negative", or "neutral"
- score must be a float between -1.0 (very negative) and 1.0 (very positive), 0 for neutral
- category must be one of: {', '.join(EVENT_CATEGORIES)}
- insight must focus on the investment implications, not just repeat the headline
- index must match the article number minus 1 (0-based)
- Analyze ALL {len(articles)} articles
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.strip()

            # Limpiar markdown si el modelo lo incluye
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            return json.loads(raw)

        except json.JSONDecodeError as e:
            print(f"[NewsAgent] Error parseando JSON de Groq: {e}")
            return []
        except Exception as e:
            print(f"[NewsAgent] Error en análisis Groq: {e}")
            return []

    def run(self, ticker: str) -> dict:
        articles = get_news(ticker)

        if not articles:
            return {
                "ticker":          ticker,
                "articles":        [],
                "sentiment_score": 0,
                "summary":         "No news found.",
                "key_events":      [],
            }

        # Obtener nombre de empresa para el prompt
        try:
            import yfinance as yf
            info         = yf.Ticker(ticker).info
            company_name = info.get("longName") or info.get("shortName") or ticker
        except Exception:
            company_name = ticker

        # Análisis con Groq
        groq_results = self.analyze_with_groq(ticker, company_name, articles)

        # Mapear resultados de Groq a los artículos
        analyzed_news = []
        scores        = []

        for i, article in enumerate(articles):
            # Buscar el análisis correspondiente por índice
            groq_data = next((r for r in groq_results if r.get("index") == i), None)

            if groq_data:
                sentiment = groq_data.get("sentiment", "neutral")
                score     = float(groq_data.get("score", 0))
                category  = groq_data.get("category", "other")
                insight   = groq_data.get("insight", "")
            else:
                # Fallback si Groq no analizó este artículo
                sentiment = "neutral"
                score     = 0.0
                category  = "other"
                insight   = ""

            scores.append(score)

            analyzed_news.append({
                "title":       article.get("title", ""),
                "description": article.get("description", ""),
                "url":         article.get("url", ""),
                "source":      article.get("source", {}),
                "publishedAt": article.get("publishedAt", ""),
                "sentiment":   sentiment,
                "score":       round(score, 4),
                "category":    category,
                "insight":     insight,
            })

        aggregate_score = round(sum(scores) / len(scores), 4) if scores else 0

        # Extraer eventos clave (los más relevantes por score absoluto)
        key_events = sorted(
            [a for a in analyzed_news if a["insight"]],
            key=lambda x: abs(x["score"]),
            reverse=True
        )[:3]

        return {
            "ticker":          ticker,
            "articles":        analyzed_news,
            "sentiment_score": aggregate_score,
            "summary":         f"Analyzed {len(analyzed_news)} articles via Groq LLM.",
            "key_events":      key_events,
            "company_name":    company_name,
        }