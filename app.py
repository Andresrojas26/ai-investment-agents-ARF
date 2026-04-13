import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_system, setup_dependencies
from agents.portfolio_agent import PortfolioAgent
from agents.backtesting_agent import BacktestingAgent
from agents.benchmark_agent import BenchmarkAgent

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ARF Investment Terminal",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── ESTILOS PROFESIONALES ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #080c10;
    color: #c9d1d9;
}
.main { background-color: #080c10; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; }

/* Ocultar elementos de Streamlit */
#MainMenu, footer, header { visibility: hidden; }

/* ── HEADER ── */
.terminal-header {
    border-bottom: 1px solid #1e2d3d;
    padding-bottom: 1.2rem;
    margin-bottom: 2rem;
}
.terminal-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    font-weight: 500;
    color: #58a6ff;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0;
}
.terminal-subtitle {
    font-size: 0.78rem;
    color: #484f58;
    margin-top: 0.3rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── SECCIÓN ── */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    color: #484f58;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-left: 2px solid #1e2d3d;
    padding-left: 0.6rem;
    margin-bottom: 1rem;
    margin-top: 0.5rem;
}

/* ── RANK CARD ── */
.rank-card {
    background: #0d1117;
    border: 1px solid #1e2d3d;
    border-radius: 4px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.rank-number {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #484f58;
    min-width: 2rem;
}
.rank-ticker {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1rem;
    font-weight: 500;
    color: #e6edf3;
    min-width: 5rem;
}
.rank-right {
    text-align: right;
}
.rank-confidence {
    font-size: 0.75rem;
    color: #484f58;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── BADGES DE DECISIÓN ── */
.badge {
    display: inline-block;
    padding: 0.2rem 0.75rem;
    border-radius: 2px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.06em;
}
.badge-buy    { background: #0d2218; color: #3fb950; border: 1px solid #238636; }
.badge-sell   { background: #2d0f0f; color: #f85149; border: 1px solid #da3633; }
.badge-hold   { background: #1f1a0a; color: #d29922; border: 1px solid #9e6a03; }
.badge-neutral{ background: #161b22; color: #8b949e; border: 1px solid #30363d; }

/* ── TABLA DE RATIOS ── */
.ratio-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid #0d1117;
    font-size: 0.88rem;
}
.ratio-label {
    color: #8b949e;
    font-size: 0.82rem;
}
.ratio-value {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 500;
    color: #e6edf3;
    font-size: 0.88rem;
}
.value-positive { color: #3fb950; }
.value-negative { color: #f85149; }
.value-neutral  { color: #e6edf3; }
.value-warning  { color: #d29922; }

/* ── MÉTRICAS ── */
.metric-block {
    background: #0d1117;
    border: 1px solid #1e2d3d;
    border-radius: 4px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
}
.metric-label {
    font-size: 0.72rem;
    color: #484f58;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 0.3rem;
}
.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.4rem;
    font-weight: 500;
    color: #e6edf3;
}
.metric-value-positive { color: #3fb950; }
.metric-value-negative { color: #f85149; }

/* ── PORTAFOLIO ── */
.portfolio-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 0;
    border-bottom: 1px solid #0d1117;
}
.portfolio-ticker {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.95rem;
    font-weight: 500;
    color: #e6edf3;
}
.portfolio-alloc {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.88rem;
    color: #58a6ff;
}
.portfolio-bar-bg {
    background: #161b22;
    border-radius: 1px;
    height: 3px;
    margin-top: 0.4rem;
    width: 100%;
}
.portfolio-bar-fill {
    background: #1f6feb;
    border-radius: 1px;
    height: 3px;
}

/* ── ALERTAS ── */
.alert-card {
    background: #1a0e0e;
    border: 1px solid #da3633;
    border-left: 3px solid #da3633;
    border-radius: 4px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
}
.alert-ticker {
    font-family: 'IBM Plex Mono', monospace;
    color: #f85149;
    font-weight: 500;
}

/* ── NOTICIAS ── */
.news-item {
    padding: 0.75rem 0;
    border-bottom: 1px solid #0d1117;
}
.news-title {
    font-size: 0.88rem;
    color: #58a6ff;
    text-decoration: none;
    line-height: 1.4;
}
.news-meta {
    font-size: 0.72rem;
    color: #484f58;
    margin-top: 0.25rem;
    font-family: 'IBM Plex Mono', monospace;
}
.news-sentiment-pos { color: #3fb950; font-size: 0.72rem; }
.news-sentiment-neg { color: #f85149; font-size: 0.72rem; }
.news-sentiment-neu { color: #d29922; font-size: 0.72rem; }

/* ── EXPANDER ── */
.stExpander {
    background: #0d1117 !important;
    border: 1px solid #1e2d3d !important;
    border-radius: 4px !important;
    margin-bottom: 0.5rem !important;
}
summary { color: #8b949e !important; }

/* ── DIVIDER ── */
.divider {
    border: none;
    border-top: 1px solid #1e2d3d;
    margin: 2rem 0;
}

/* ── PEGY ── */
.pegy-block {
    background: #0d1117;
    border: 1px solid #1e2d3d;
    border-radius: 4px;
    padding: 0.75rem 1rem;
    margin-top: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.pegy-label {
    font-size: 0.82rem;
    color: #8b949e;
}
.pegy-interpretation {
    font-size: 0.72rem;
    color: #484f58;
    margin-top: 0.15rem;
}

/* ── ANÁLISIS IA ── */
.ai-analysis {
    background: #0d1117;
    border: 1px solid #1e2d3d;
    border-left: 2px solid #58a6ff;
    border-radius: 4px;
    padding: 0.9rem 1rem;
    font-size: 0.85rem;
    line-height: 1.6;
    color: #8b949e;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 1px solid #1e2d3d;
}
.stButton > button {
    background: #1f6feb;
    color: #ffffff;
    border: none;
    border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    padding: 0.5rem 1rem;
    width: 100%;
    transition: background 0.15s;
}
.stButton > button:hover { background: #388bfd; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def decision_badge(rec: str) -> str:
    rec_upper = str(rec).upper()
    if "BUY" in rec_upper or "COMPRAR" in rec_upper:
        return f'<span class="badge badge-buy">BUY</span>'
    elif "SELL" in rec_upper or "VENDER" in rec_upper:
        return f'<span class="badge badge-sell">SELL</span>'
    elif "HOLD" in rec_upper or "MANTENER" in rec_upper:
        return f'<span class="badge badge-hold">HOLD</span>'
    return f'<span class="badge badge-neutral">{rec}</span>'

def parse_confidence(conf) -> float:
    try:
        return float(str(conf).replace('%', '').strip())
    except:
        return 0.0

def color_value(val, key="") -> str:
    """Formatea un valor numérico con color según si es positivo/negativo."""
    if val is None:
        return '<span class="ratio-value value-neutral">—</span>'
    try:
        if "fcf" in key or (isinstance(val, (int, float)) and abs(val) > 5000):
            formatted = f"${val:,.0f}"
            css = "value-positive" if val > 0 else "value-negative"
        elif isinstance(val, (int, float)) and -1 < val < 1:
            formatted = f"{val*100:.2f}%"
            if key in ("pe", "debt_to_equity", "volatility"):
                css = "value-neutral"
            else:
                css = "value-positive" if val > 0 else "value-negative"
        else:
            formatted = f"{val:.2f}"
            css = "value-neutral"
        return f'<span class="ratio-value {css}">{formatted}</span>'
    except:
        return f'<span class="ratio-value value-neutral">{val}</span>'

def metric_html(label: str, value: str, positive: bool = None) -> str:
    if positive is True:
        css = "metric-value-positive"
    elif positive is False:
        css = "metric-value-negative"
    else:
        css = ""
    return f"""
    <div class="metric-block">
        <div class="metric-label">{label}</div>
        <div class="metric-value {css}">{value}</div>
    </div>"""

LABEL_MAP = {
    "pe":             "P / E Ratio",
    "roe":            "ROE",
    "debt_to_equity": "Debt / Equity",
    "revenue_growth": "Revenue Growth",
    "fcf":            "Free Cash Flow",
    "momentum":       "Momentum 6M",
    "volatility":     "Volatility (Ann.)",
    "eps_growth":     "EPS Growth",
    "dividend_yield": "Dividend Yield",
}


# ── CACHÉ ─────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cached_run_system(ticker, risk_level, capital):
    return run_system(ticker, risk_level=risk_level, capital=int(capital))


# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "all_reports"    not in st.session_state:
    st.session_state.all_reports    = None
if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = None


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="terminal-header">
    <div class="terminal-title">ARF · Investment Terminal</div>
    <div class="terminal-subtitle">Multi-Agent Analysis System &nbsp;·&nbsp; Andrés Rojas F. &nbsp;·&nbsp; Civil Industrial Engineering</div>
</div>
""", unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("**PARAMETERS**")
risk          = st.sidebar.select_slider("Risk Profile", options=["low", "medium", "high"], value="medium")
capital       = st.sidebar.number_input("Initial Capital ($)", value=10000, step=1000)
tickers_input = st.sidebar.text_input("Tickers", "AAPL, MSFT, NVDA, F")
run_btn       = st.sidebar.button("RUN ANALYSIS")


# ── EJECUCIÓN ─────────────────────────────────────────────────────────────────
if run_btn:
    setup_dependencies()
    tickers = [t.strip().upper() for t in tickers_input.split(",")]

    with st.spinner("Processing..."):
        reports = []
        for ticker in tickers:
            try:
                res = cached_run_system(ticker, risk, capital)
                reports.append(res)
            except Exception as e:
                st.error(f"{ticker}: {str(e)}")

        if reports:
            p_agent       = PortfolioAgent()
            portfolio_res = p_agent.run(reports, capital)
            bt_agent      = BacktestingAgent()
            bt_res        = bt_agent.run(portfolio_res["portfolio"])
            bench_agent   = BenchmarkAgent()
            bench_res     = bench_agent.run(bt_res["portfolio_return"])

            st.session_state.all_reports    = reports
            st.session_state.portfolio_data = {
                "portfolio_res": portfolio_res,
                "bt_res":        bt_res,
                "bench_res":     bench_res,
            }


# ── RESULTADOS ────────────────────────────────────────────────────────────────
if st.session_state.all_reports:
    all_reports = st.session_state.all_reports
    pd_data     = st.session_state.portfolio_data

    # ════════════════════════════════════════════════════════
    # SECCIÓN 1 — RECOMMENDATIONS
    # ════════════════════════════════════════════════════════
    st.markdown('<div class="section-label">Recommendations</div>', unsafe_allow_html=True)

    sorted_reports = sorted(
        all_reports,
        key=lambda x: parse_confidence(x['decision']['confidence']),
        reverse=True
    )

    for i, res in enumerate(sorted_reports):
        rec  = res['decision']['recommendation']
        conf = res['decision']['confidence']
        st.markdown(f"""
        <div class="rank-card">
            <div style="display:flex; align-items:center; gap:1.25rem;">
                <span class="rank-number">#{i+1}</span>
                <span class="rank-ticker">{res['ticker']}</span>
                {decision_badge(rec)}
            </div>
            <div class="rank-right">
                <div class="rank-confidence">Confidence &nbsp; {conf}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # SECCIÓN 2 — ALERTS
    # ════════════════════════════════════════════════════════
    active_alerts = [
        (r['ticker'], r['alert'])
        for r in all_reports
        if r.get('alert', {}).get('alert') is True
    ]
    if active_alerts:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Active Alerts</div>', unsafe_allow_html=True)
        for ticker_name, alert in active_alerts:
            st.markdown(f"""
            <div class="alert-card">
                <span class="alert-ticker">{ticker_name}</span>
                &nbsp;·&nbsp; {alert['type']}: {alert['message']}
            </div>
            """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # SECCIÓN 3 — PORTFOLIO
    # ════════════════════════════════════════════════════════
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Portfolio Allocation</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.78rem;color:#484f58;margin-bottom:0.75rem;font-family:\'IBM Plex Mono\',monospace;">Capital: ${capital:,.0f}</div>', unsafe_allow_html=True)

    portfolio        = pd_data["portfolio_res"]["portfolio"]
    sorted_portfolio = sorted(portfolio, key=lambda x: x["weight"], reverse=True)

    for i, p in enumerate(sorted_portfolio):
        pct   = p["weight"] * 100
        alloc = p["allocation"]
        bar_w = int(pct)
        st.markdown(f"""
        <div class="portfolio-row">
            <div>
                <span style="font-size:0.72rem;color:#484f58;font-family:'IBM Plex Mono',monospace;">#{i+1} &nbsp;</span>
                <span class="portfolio-ticker">{p['ticker']}</span>
            </div>
            <div style="text-align:right;">
                <span class="portfolio-alloc">{pct:.1f}%</span>
                <span style="font-size:0.78rem;color:#484f58;font-family:'IBM Plex Mono',monospace;"> &nbsp; ${alloc:,.0f}</span>
            </div>
        </div>
        <div class="portfolio-bar-bg">
            <div class="portfolio-bar-fill" style="width:{bar_w}%;"></div>
        </div>
        """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # SECCIÓN 4 — BACKTESTING
    # ════════════════════════════════════════════════════════
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Backtesting</div>', unsafe_allow_html=True)

    bt_res   = pd_data["bt_res"]
    port_ret = bt_res['portfolio_return'] * 100
    sharpe   = bt_res['sharpe_ratio']
    vol      = bt_res['volatility']

    st.markdown(metric_html("Portfolio Return", f"{port_ret:.2f}%", positive=port_ret > 0), unsafe_allow_html=True)
    st.markdown(metric_html("Sharpe Ratio",     f"{sharpe:.2f}",   positive=sharpe > 1), unsafe_allow_html=True)
    st.markdown(metric_html("Annualized Volatility", f"{vol:.4f}"), unsafe_allow_html=True)

    # Retornos individuales
    st.markdown('<div style="margin-top:1.25rem;">', unsafe_allow_html=True)
    for r in bt_res.get("stocks", []):
        ret = r['return'] * 100
        css = "value-positive" if ret > 0 else "value-negative"
        st.markdown(f"""
        <div class="ratio-row">
            <span class="ratio-label">{r['ticker']}</span>
            <span class="ratio-value {css}">{ret:+.2f}%</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # SECCIÓN 5 — ALPHA
    # ════════════════════════════════════════════════════════
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Alpha vs Market</div>', unsafe_allow_html=True)

    bench_res  = pd_data["bench_res"]
    p_ret      = bench_res['portfolio_return'] * 100
    b_ret      = bench_res['benchmark_return']  * 100
    alpha_val  = bench_res['alpha'] * 100

    st.markdown(metric_html("Portfolio",  f"{p_ret:+.2f}%",   positive=p_ret > 0),   unsafe_allow_html=True)
    st.markdown(metric_html("S&P 500",    f"{b_ret:+.2f}%",   positive=b_ret > 0),   unsafe_allow_html=True)
    st.markdown(metric_html("Alpha",      f"{alpha_val:+.2f}%", positive=alpha_val > 0), unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # SECCIÓN 6 — ANÁLISIS DETALLADO
    # ════════════════════════════════════════════════════════
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Asset Analysis</div>', unsafe_allow_html=True)

    for res in all_reports:
        rec   = res['decision']['recommendation']
        label = f"{res['ticker']}  ·  {rec}"
        with st.expander(label, expanded=False):

            # Ratios
            st.markdown('<div style="margin-bottom:0.5rem;font-size:0.72rem;color:#484f58;text-transform:uppercase;letter-spacing:0.08em;font-family:\'IBM Plex Mono\',monospace;">Key Ratios</div>', unsafe_allow_html=True)
            r = res['financials'].get('ratios', {})
            for key, val in r.items():
                name = LABEL_MAP.get(key, key.upper())
                st.markdown(f"""
                <div class="ratio-row">
                    <span class="ratio-label">{name}</span>
                    {color_value(val, key)}
                </div>
                """, unsafe_allow_html=True)

            # PEGY
            pegy = res['analysis'].get('pegy')
            if pegy is not None:
                if pegy < 1:
                    pegy_css = "value-positive"
                    pegy_txt = "Potentially undervalued"
                elif pegy <= 2:
                    pegy_css = "value-warning"
                    pegy_txt = "Fair valuation"
                else:
                    pegy_css = "value-negative"
                    pegy_txt = "Potentially overvalued"

                st.markdown(f"""
                <div class="pegy-block">
                    <div>
                        <div class="pegy-label">PEGY Ratio</div>
                        <div class="pegy-interpretation">{pegy_txt}</div>
                    </div>
                    <span class="ratio-value {pegy_css}">{pegy}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="pegy-block">
                    <div class="pegy-label">PEGY Ratio</div>
                    <span class="ratio-value value-neutral">N/A</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Análisis IA
            st.markdown('<div style="font-size:0.72rem;color:#484f58;text-transform:uppercase;letter-spacing:0.08em;font-family:\'IBM Plex Mono\',monospace;margin-bottom:0.5rem;">AI Analysis</div>', unsafe_allow_html=True)
            explanation = res['explainability']['explanation']
            st.markdown(f'<div class="ai-analysis">{explanation}</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Sentimiento
            score = res['sentiment']['sentiment_score']
            if score > 0.15:
                sent_css  = "value-positive"
                sent_label = "POSITIVE"
            elif score < -0.15:
                sent_css  = "value-negative"
                sent_label = "NEGATIVE"
            else:
                sent_css  = "value-warning"
                sent_label = "NEUTRAL"

            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
                <div style="font-size:0.72rem;color:#484f58;text-transform:uppercase;letter-spacing:0.08em;font-family:'IBM Plex Mono',monospace;">News Sentiment</div>
                <span class="ratio-value {sent_css}" style="font-size:0.8rem;">{sent_label} &nbsp; {score:+.2f}</span>
            </div>
            """, unsafe_allow_html=True)

            # Noticias
            articles = res['sentiment'].get('articles', [])
            if not articles:
                st.markdown('<div style="font-size:0.82rem;color:#484f58;">No recent news found.</div>', unsafe_allow_html=True)
            else:
                for art in articles[:5]:
                    link         = art.get('url', '')
                    titulo       = art.get('title', 'No title')
                    fuente       = art.get('source', {}).get('name', 'Unknown')
                    published    = art.get('publishedAt', '')[:10]
                    art_sent     = art.get('sentiment', 'neutral')

                    if art_sent == 'positive':
                        dot = '<span class="news-sentiment-pos">&#9679;</span>'
                    elif art_sent == 'negative':
                        dot = '<span class="news-sentiment-neg">&#9679;</span>'
                    else:
                        dot = '<span class="news-sentiment-neu">&#9679;</span>'

                    if link.startswith('http'):
                        title_html = f'<a href="{link}" target="_blank" class="news-title">{titulo}</a>'
                    else:
                        title_html = f'<span class="news-title" style="color:#8b949e;">{titulo}</span>'

                    st.markdown(f"""
                    <div class="news-item">
                        {dot} &nbsp; {title_html}
                        <div class="news-meta">{fuente} &nbsp;·&nbsp; {published}</div>
                    </div>
                    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:4rem 0;color:#484f58;">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.85rem;letter-spacing:0.08em;">
            Configure parameters and run analysis
        </div>
    </div>
    """, unsafe_allow_html=True)