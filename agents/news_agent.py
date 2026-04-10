# agents/news_agent.py
from agents.base_agent import BaseAgent
from tools.news_fetcher import get_news
from textblob import TextBlob


class NewsAgent(BaseAgent):
    def __init__(self):
        super().__init__("News Agent")

    def analyze_sentiment(self, text):
        polarity = TextBlob(text).sentiment.polarity

        if polarity > 0:
            sentiment = "positive"
        elif polarity < 0:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return sentiment, polarity

    def run(self, ticker):
        news = get_news(ticker)

        analyzed_news = []
        scores = []

        for article in news:
            sentiment, score = self.analyze_sentiment(article["title"] or "")

            analyzed_news.append({
                "title": article["title"],
                "sentiment": sentiment,
                "score": score
            })

            scores.append(score)

        aggregate_score = sum(scores) / len(scores) if scores else 0

        return {
            "ticker": ticker,
            "articles": analyzed_news,
            "sentiment_score": aggregate_score,
            "summary": "News sentiment analyzed"
        }

