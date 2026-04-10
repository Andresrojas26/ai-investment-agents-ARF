import requests

API_KEY = "966de9cfce8a4ab18b57222bad462146"

def get_news(ticker):
    url = f"https://newsapi.org/v2/everything?q={ticker}&language=en&pageSize=5&apiKey={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"Error de NewsAPI: {data.get('message')}")
            return []

        articles = data.get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "description": a.get("description", "")
            }
            for a in articles
        ]
    except Exception as e:
        print(f"Error de conexión en NewsAPI: {e}")
        return []