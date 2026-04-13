from agents.base_agent import BaseAgent
from tools.news_fetcher import get_news
from textblob import TextBlob


class NewsAgent(BaseAgent):
    def __init__(self):
        super().__init__("News Agent")

    def analyze_sentiment(self, title: str, description: str = "") -> tuple:
        # ✅ Analiza título + description para mayor contexto
        text     = f"{title}. {description}".strip()
        polarity = TextBlob(text).sentiment.polarity

        if polarity > 0.15:
            sentiment = "positive"
        elif polarity < -0.15:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return sentiment, round(polarity, 4)

    def run(self, ticker: str) -> dict:
        news = get_news(ticker)

        analyzed_news = []
        scores        = []

        for article in news:
            title       = article.get("title", "")
            description = article.get("description", "")

            sentiment, score = self.analyze_sentiment(title, description)

            # ✅ url y source se preservan para que lleguen a app.py
            analyzed_news.append({
                "title":       title,
                "description": description,
                "url":         article.get("url", ""),
                "source":      article.get("source", {}),
                "publishedAt": article.get("publishedAt", ""),
                "sentiment":   sentiment,
                "score":       score,
            })

            scores.append(score)

        aggregate_score = round(sum(scores) / len(scores), 4) if scores else 0

        return {
            "ticker":          ticker,
            "articles":        analyzed_news,
            "sentiment_score": aggregate_score,
            "summary":         "News sentiment analyzed"
        }