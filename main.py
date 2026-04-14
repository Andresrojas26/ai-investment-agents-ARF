import os
import sys
import nltk
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.data_agent import DataAgent
from agents.news_agent import NewsAgent
from agents.analysis_agent import AnalysisAgent
from agents.decision_agent import DecisionAgent
from agents.user_profile_agent import UserProfileAgent
from agents.explainability_agent import ExplainabilityAgent
from agents.smart_alert_agent import SmartAlertAgent
from agents.portfolio_agent import PortfolioAgent
from agents.backtesting_agent import BacktestingAgent
from agents.benchmark_agent import BenchmarkAgent


def setup_dependencies():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
        nltk.download('brown')
        try:
            from textblob import download_corpora
            download_corpora.main()
        except Exception as e:
            print(f"[WARNING] textblob corpora no descargado: {e}")


def run_system(ticker, risk_level="medium", capital=10000, investment_horizon="long"):

    user_agent   = UserProfileAgent()
    user_profile = user_agent.run(
        risk_level=risk_level,
        investment_horizon=investment_horizon,
        capital=capital
    )

    data_agent  = DataAgent()
    data_result = data_agent.run(ticker)

    news_agent  = NewsAgent()
    news_result = news_agent.run(ticker)

    analysis_agent  = AnalysisAgent()
    analysis_result = analysis_agent.run(data_result, news_result)

    decision_agent  = DecisionAgent()
    decision_result = decision_agent.run(analysis_result, user_profile)

    explain_agent  = ExplainabilityAgent()
    explain_result = explain_agent.run(analysis_result)

    alert_agent  = SmartAlertAgent()
    alert_result = alert_agent.run(analysis_result)

    return {
        "ticker":        ticker,
        "user":          user_profile,
        "financials":    data_result,
        "sentiment":     news_result,
        "analysis":      analysis_result,
        "decision":      decision_result,
        "explainability": explain_result,
        "alert":         alert_result
    }


# ✅ Ejecución paralela de tickers
def run_all_tickers(tickers: list, risk_level: str = "medium", capital: int = 10000) -> list:
    results = []
    errors  = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_system, ticker, risk_level, capital): ticker
            for ticker in tickers
        }
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                results.append(future.result())
            except Exception as e:
                errors.append(ticker)
                print(f"[ERROR] {ticker}: {e}")

    if errors:
        print(f"[WARNING] Tickers fallidos: {errors}")

    # Mantener orden original
    order = {t: i for i, t in enumerate(tickers)}
    results.sort(key=lambda r: order.get(r["ticker"], 999))
    return results


if __name__ == "__main__":
    tickers = ["AAPL", "TSLA", "MSFT"]

    try:
        setup_dependencies()

        all_reports = run_all_tickers(tickers, risk_level="medium", capital=10000)

        portfolio_agent  = PortfolioAgent()
        capital          = all_reports[0]["user"]["capital"]
        risk_level       = all_reports[0]["user"]["risk_level"]
        portfolio_result = portfolio_agent.run(all_reports, capital, risk_level=risk_level)

        print("\n" + "="*60)
        print("💼 PORTAFOLIO")
        print("="*60)
        for p in portfolio_result["portfolio"]:
            print(f"{p['ticker']} → {p['weight']*100:.1f}% (${p['allocation']})")

        backtest        = BacktestingAgent()
        backtest_result = backtest.run(portfolio_result["portfolio"])

        print("\n📈 BACKTEST")
        print("="*60)
        for r in backtest_result["stocks"]:
            print(f"{r['ticker']} → {r['return']*100:.2f}%")
        print(f"\nRetorno:      {backtest_result['portfolio_return']*100:.2f}%")
        print(f"Volatilidad:  {backtest_result['volatility']:.4f}")
        print(f"Sharpe:       {backtest_result['sharpe_ratio']:.2f}")
        print(f"Sortino:      {backtest_result['sortino_ratio']:.2f}")
        print(f"Max Drawdown: {backtest_result['max_drawdown']*100:.2f}%")
        print(f"VaR 95%:      {backtest_result['var_95']*100:.2f}%")
        print(f"CVaR 95%:     {backtest_result['cvar_95']*100:.2f}%")

        benchmark = BenchmarkAgent()
        bench     = benchmark.run(
            portfolio_return=backtest_result["portfolio_return"],
            portfolio_beta=backtest_result.get("portfolio_beta", 1.0)
        )

        print("\n📊 VS MERCADO")
        print("="*60)
        print(f"Portafolio:      {bench['portfolio_return']*100:.2f}%")
        print(f"S&P 500:         {bench['benchmark_return']*100:.2f}%")
        print(f"Alpha simple:    {bench['alpha']*100:.2f}%")
        print(f"Jensen's Alpha:  {bench['jensens_alpha']*100:.2f}%\n")

    except Exception as e:
        print(f"[ERROR]: {str(e)}")