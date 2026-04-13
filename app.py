import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_system, setup_dependencies
from agents.portfolio_agent import PortfolioAgent
from agents.backtesting_agent import BacktestingAgent
from agents.benchmark_agent import BenchmarkAgent

# ── CONFIGURACIÓN ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Terminal IA - Andrés Rojas",
    layout="centered",          # ✅ FIX 7: era "wide"
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffcc; }
    .stExpander { border: 1px solid #30363d; border-radius: 8px; margin-bottom: 1rem; }
    .stCaption  { font-size: 0.85rem; color: #8b949e; }
    .rank-card  {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 AI Investment Agent")
st.caption("Estrategia y Análisis Multi-Agente | Andrés Rojas - Civil Industrial Engineering")


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Panel de Control")
risk    = st.sidebar.select_slider("Perfil de Riesgo", options=["low", "medium", "high"], value="medium")
capital = st.sidebar.number_input("Capital Inicial ($)", value=10000, step=1000)
tickers_input = st.sidebar.text_input("Acciones (ej: AAPL, NVDA, TSLA)", "AAPL, MSFT, NVDA, F")


# ── CACHÉ ─────────────────────────────────────────────────────────────────────
# ✅ FIX 3: evita refetchear si el usuario repite los mismos parámetros
@st.cache_data(show_spinner=False)
def cached_run_system(ticker, risk_level, capital):
    return run_system(ticker, risk_level=risk_level, capital=int(capital))


# ── HELPERS ───────────────────────────────────────────────────────────────────
DECISION_ICONS = {
    "BUY": "🟢", "COMPRAR": "🟢",
    "SELL": "🔴", "VENDER": "🔴",
    "HOLD": "🟡", "MANTENER": "🟡",
}

def decision_icon(rec):
    rec_upper = str(rec).upper()
    for key, icon in DECISION_ICONS.items():
        if key in rec_upper:
            return icon
    return "⚪"

def parse_confidence(conf):
    """Convierte el valor de confianza a float para poder ordenar."""
    try:
        return float(str(conf).replace('%', '').strip())
    except:
        return 0.0

LABEL_MAP = {
    "pe":             "P/E Ratio",
    "roe":            "ROE (Retorno s/ Patrimonio)",
    "debt_to_equity": "Ratio Deuda / Capital",
    "revenue_growth": "Crecimiento Ingresos",
    "fcf":            "Free Cash Flow",
    "momentum":       "Momentum (6m)",
    "volatility":     "Volatilidad Anual",
}

def format_ratio(key, val):
    if val is None:
        return "N/A"
    try:
        if "fcf" in key or (isinstance(val, (int, float)) and val > 5000):
            return f"${val:,.0f}"
        elif isinstance(val, (int, float)) and -1 < val < 1:
            return f"{val*100:.2f}%"
        else:
            return f"{val:.2f}"
    except:
        return str(val)


# ── SESSION STATE ─────────────────────────────────────────────────────────────
# ✅ FIX 2: resultados guardados en sesión; no desaparecen al interactuar
if "all_reports"   not in st.session_state:
    st.session_state.all_reports   = None
if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = None


# ── BOTÓN DE EJECUCIÓN ────────────────────────────────────────────────────────
if st.sidebar.button("🚀 Iniciar Análisis"):
    setup_dependencies()
    tickers = [t.strip().upper() for t in tickers_input.split(",")]

    with st.spinner("Los agentes están procesando datos en tiempo real..."):
        reports = []
        for ticker in tickers:
            try:
                # ✅ FIX 1: risk y capital del sidebar se pasan al sistema
                res = cached_run_system(ticker, risk, capital)
                reports.append(res)
            except Exception as e:
                st.error(f"Error analizando {ticker}: {str(e)}")

        if reports:
            p_agent  = PortfolioAgent()
            portfolio_res = p_agent.run(reports, capital)

            bt_agent = BacktestingAgent()
            bt_res   = bt_agent.run(portfolio_res["portfolio"])

            bench_agent = BenchmarkAgent()
            bench_res   = bench_agent.run(bt_res["portfolio_return"])

            st.session_state.all_reports   = reports
            st.session_state.portfolio_data = {
                "portfolio_res": portfolio_res,
                "bt_res":        bt_res,
                "bench_res":     bench_res,
            }


# ── RENDERIZADO DE RESULTADOS ─────────────────────────────────────────────────
if st.session_state.all_reports:
    all_reports = st.session_state.all_reports
    pd_data     = st.session_state.portfolio_data

    # ════════════════════════════════════════════════════════
    # 🎯 SECCIÓN 1: RANKING DE DECISIONES
    # ════════════════════════════════════════════════════════
    # ✅ FIX 8: ranking ordenado por confianza con semáforos
    st.header("🎯 Ranking de Recomendaciones")
    st.caption("Ordenado por nivel de confianza del agente")

    sorted_reports = sorted(
        all_reports,
        key=lambda x: parse_confidence(x['decision']['confidence']),
        reverse=True
    )

    for i, res in enumerate(sorted_reports):
        rec  = res['decision']['recommendation']
        conf = res['decision']['confidence']
        icon = decision_icon(rec)
        st.markdown(f"""
        <div class="rank-card">
            <span style="font-size:1.1rem;"><strong>#{i+1} &nbsp; {res['ticker']}</strong></span><br>
            <span style="font-size:1.3rem;">{icon}</span> &nbsp;<strong>{rec}</strong>
            &nbsp;·&nbsp; <span style="color:#8b949e;">Confianza: {conf}</span>
        </div>
        """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # 🚨 SECCIÓN 2: ALERTAS ACTIVAS
    # ════════════════════════════════════════════════════════
    active_alerts = [
        (r['ticker'], r['alert'])
        for r in all_reports
        if r.get('alert', {}).get('alert') is True
    ]

    if active_alerts:
        st.divider()
        st.header("🚨 Alertas Activas")
        for ticker_name, alert in active_alerts:
            st.warning(f"**{ticker_name}** · {alert['type']}: {alert['message']}")

    # ════════════════════════════════════════════════════════
    # 💼 SECCIÓN 3: PORTAFOLIO
    # ════════════════════════════════════════════════════════
    st.divider()
    st.header("💼 Portafolio Sugerido")
    st.caption(f"Capital total: ${capital:,.0f}")

    portfolio = pd_data["portfolio_res"]["portfolio"]
    sorted_portfolio = sorted(portfolio, key=lambda x: x["weight"], reverse=True)

    for i, p in enumerate(sorted_portfolio):
        pct   = p["weight"] * 100
        alloc = p["allocation"]
        st.markdown(f"**#{i+1} &nbsp; {p['ticker']}** — {pct:.1f}% &nbsp;·&nbsp; ${alloc:,.0f}")
        st.progress(float(p["weight"]))

    # ════════════════════════════════════════════════════════
    # 📈 SECCIÓN 4: BACKTESTING
    # ════════════════════════════════════════════════════════
    st.divider()
    st.header("📈 Backtesting")

    bt_res = pd_data["bt_res"]

    # ✅ FIX 7: métricas en columna vertical, sin st.columns
    st.metric("Retorno del Portafolio", f"{bt_res['portfolio_return']*100:.2f}%")
    st.metric("Sharpe Ratio",           f"{bt_res['sharpe_ratio']:.2f}")
    st.metric("Volatilidad",            f"{bt_res['volatility']:.4f}")

    st.caption("Retorno individual por acción:")
    for r in bt_res.get("stocks", []):
        ret  = r['return'] * 100
        icon = "🟢" if ret > 0 else "🔴"
        st.markdown(f"{icon} &nbsp; **{r['ticker']}** → {ret:.2f}%")

    # ════════════════════════════════════════════════════════
    # 🏆 SECCIÓN 5: ALPHA VS MERCADO
    # ════════════════════════════════════════════════════════
    st.divider()
    st.header("🏆 Alpha vs Mercado")

    bench_res = pd_data["bench_res"]
    port_ret  = bench_res['portfolio_return'] * 100
    bench_ret = bench_res['benchmark_return'] * 100
    alpha_val = bench_res['alpha'] * 100
    delta_str = f"{'↑' if alpha_val > 0 else '↓'} vs S&P 500"

    st.metric("Tu Portafolio",   f"{port_ret:.2f}%")
    st.metric("S&P 500",         f"{bench_ret:.2f}%")
    st.metric("Alpha Generado",  f"{alpha_val:.2f}%", delta=delta_str)

    # ════════════════════════════════════════════════════════
    # 🔍 SECCIÓN 6: ANÁLISIS DETALLADO
    # ════════════════════════════════════════════════════════
    st.divider()
    st.header("🔍 Análisis Detallado por Activo")
    st.caption("Expandí cada activo para ver ratios, análisis IA y noticias")

    for res in all_reports:
        label = f"📊 {res['ticker']} — {decision_icon(res['decision']['recommendation'])} {res['decision']['recommendation']}"
        with st.expander(label, expanded=False):

            # Ratios financieros
            st.subheader("📉 Ratios Clave")
            r = res['financials'].get('ratios', {})
            for key, val in r.items():
                name  = LABEL_MAP.get(key, key.upper())
                v_str = format_ratio(key, val)
                st.write(f"**{name}:** {v_str}")

            st.markdown("---")

            # Análisis IA
            st.markdown("**💡 Análisis de la IA:**")
            st.info(res['explainability']['explanation'])

            st.markdown("---")

            # Sentimiento y noticias (✅ FIX 7: sin columnas, flujo vertical)
            st.subheader("📰 Sentimiento de Noticias")
            score = res['sentiment']['sentiment_score']
            if score > 0.15:
                st.success(f"Sentimiento Positivo: {score:.2f} ✅")
            elif score < -0.15:
                st.error(f"Sentimiento Negativo: {score:.2f} ⚠️")
            else:
                st.warning(f"Sentimiento Neutral: {score:.2f} ⚖️")

            articles = res['sentiment'].get('articles', [])
            if not articles:
                st.write("No se encontraron noticias recientes.")
            else:
                for art in articles[:5]:
                    link_real    = art.get('url')
                    titulo       = art.get('title', 'Noticia sin título')
                    nombre_fuente = art.get('source', {}).get('name', 'Fuente Externa')
                    if link_real and str(link_real).startswith('http'):
                        st.markdown(f"🔗 **[{titulo}]({link_real})**")
                    else:
                        st.markdown(f"🔹 {titulo}")
                    st.caption(f"Fuente: {nombre_fuente}")
                    st.divider()

else:
    st.info("Configura los tickers en el menú lateral y presiona 'Iniciar Análisis'.")