import os
import sys
import nltk

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


# ✅ FIX 1: run_system ahora acepta risk_level y capital como parámetros
def run_system(ticker, risk_level="medium", capital=10000, investment_horizon="long"):

    # 0. USER PROFILE
    user_agent = UserProfileAgent()
    user_profile = user_agent.run(
        risk_level=risk_level,
        investment_horizon=investment_horizon,
        capital=capital
    )

    # 1. DATA
    data_agent = DataAgent()
    data_result = data_agent.run(ticker)

    # 2. NEWS
    news_agent = NewsAgent()
    news_result = news_agent.run(ticker)

    # 3. ANALYSIS
    analysis_agent = AnalysisAgent()
    analysis_result = analysis_agent.run(data_result, news_result)

    # 4. DECISION
    decision_agent = DecisionAgent()
    decision_result = decision_agent.run(analysis_result, user_profile)

    # 5. EXPLAINABILITY
    explain_agent = ExplainabilityAgent()
    explain_result = explain_agent.run(analysis_result)

    # 6. ALERT
    alert_agent = SmartAlertAgent()
    alert_result = alert_agent.run(analysis_result)

    return {
        "ticker": ticker,
        "user": user_profile,
        "financials": data_result,
        "sentiment": news_result,
        "analysis": analysis_result,
        "decision": decision_result,
        "explainability": explain_result,
        "alert": alert_result
    }


if __name__ == "__main__":
    tickers = ["AAPL", "TSLA", "MSFT"]

    try:
        setup_dependencies()

        all_reports = []
        for ticker in tickers:
            report = run_system(ticker)
            all_reports.append(report)

        # ✅ FIX 5: imports eliminados aquí, ya están arriba
        portfolio_agent = PortfolioAgent()
        capital = all_reports[0]["user"]["capital"]
        portfolio_result = portfolio_agent.run(all_reports, capital)

        print("\n" + "="*60)
        print("💼 PORTAFOLIO")
        print("="*60)
        for p in portfolio_result["portfolio"]:
            print(f"{p['ticker']} → {p['weight']*100:.1f}% (${p['allocation']})")

        backtest = BacktestingAgent()
        backtest_result = backtest.run(portfolio_result["portfolio"])

        print("\n📈 BACKTEST")
        print("="*60)
        for r in backtest_result["stocks"]:
            print(f"{r['ticker']} → {r['return']*100:.2f}%")
        print(f"\nRetorno:    {backtest_result['portfolio_return']*100:.2f}%")
        print(f"Volatilidad:{backtest_result['volatility']:.4f}")
        print(f"Sharpe:     {backtest_result['sharpe_ratio']:.2f}")

        benchmark = BenchmarkAgent()
        bench = benchmark.run(backtest_result["portfolio_return"])

        print("\n📊 VS MERCADO")
        print("="*60)
        print(f"Portafolio: {bench['portfolio_return']*100:.2f}%")
        print(f"S&P 500:    {bench['benchmark_return']*100:.2f}%")
        print(f"Alpha:      {bench['alpha']*100:.2f}%\n")

    except Exception as e:
        # ✅ FIX 6: except genérico reemplazado por uno con contexto
        print(f"[ERROR]: {str(e)}")