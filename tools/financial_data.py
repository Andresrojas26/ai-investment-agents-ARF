import yfinance as yf

def get_financial_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Validamos que existan datos básicos
        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info:
            return {k: None for k in ["pe", "pb", "roe", "debt_to_equity", "revenue_growth", "fcf"]}

        return {
            "pe": info.get("trailingPE"),
            "pb": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "fcf": info.get("freeCashflow")
        }
    except Exception as e:
        print(f"Error en yfinance para {ticker}: {e}")
        return {k: None for k in ["pe", "pb", "roe", "debt_to_equity", "revenue_growth", "fcf"]}
