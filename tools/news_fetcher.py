import requests
import yfinance as yf

# ⚠️ Temporal — reemplazar por variable de entorno antes de subir a producción
NEWS_API_KEY = "966de9cfce8a4ab18b57222bad462146"


def get_company_name(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
        return info.get("longName") or info.get("shortName") or ticker
    except Exception:
        return ticker


def get_news(ticker: str) -> list:
    company = get_company_name(ticker)
    query   = f"{company} stock"

    print(f"[News Fetcher] Buscando noticias para: '{query}'")

    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={query}"
        f"&searchIn=title"
        f"&language=en"
        f"&pageSize=8"          # ✅ Más artículos para mejor análisis
        f"&sortBy=publishedAt"
        f"&apiKey={NEWS_API_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 401:
            print("[News Fetcher] ERROR 401: API key inválida o expirada.")
            return []
        if response.status_code == 429:
            print("[News Fetcher] ERROR 429: Límite de requests alcanzado.")
            return []
        if response.status_code != 200:
            print(f"[News Fetcher] ERROR {response.status_code}: {response.text[:200]}")
            return []

        data = response.json()

        if data.get("status") != "ok":
            print(f"[News Fetcher] Error en respuesta: {data.get('message')}")
            return []

        articles = data.get("articles", [])

        return [
            {
                "title":       a.get("title", ""),
                "description": a.get("description", "") or "",
                "url":         a.get("url", ""),
                "source":      a.get("source", {}),
                "publishedAt": a.get("publishedAt", ""),
            }
            for a in articles
            if a.get("title")
        ]

    except requests.exceptions.Timeout:
        print(f"[News Fetcher] Timeout al buscar noticias de '{ticker}'.")
        return []
    except Exception as e:
        print(f"[News Fetcher] Error inesperado: {e}")
        return []


def get_macro_news() -> list:
    """Obtiene noticias macroeconómicas globales."""
    queries = [
        "Federal Reserve interest rates",
        "global economy inflation GDP",
        "stock market outlook recession",
    ]

    all_articles = []

    for query in queries:
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q={query}"
            f"&searchIn=title"
            f"&language=en"
            f"&pageSize=3"
            f"&sortBy=publishedAt"
            f"&apiKey={NEWS_API_KEY}"
        )
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            if data.get("status") != "ok":
                continue
            for a in data.get("articles", []):
                if a.get("title"):
                    all_articles.append({
                        "title":       a.get("title", ""),
                        "description": a.get("description", "") or "",
                        "url":         a.get("url", ""),
                        "source":      a.get("source", {}),
                        "publishedAt": a.get("publishedAt", ""),
                    })
        except Exception:
            continue

    return all_articles