import streamlit as st
import pandas as pd
import sys
import os

# Configuración de rutas para asegurar que encuentre los módulos en la nube
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_system, setup_dependencies
from agents.portfolio_agent import PortfolioAgent
from agents.backtesting_agent import BacktestingAgent
from agents.benchmark_agent import BenchmarkAgent

# 1. CONFIGURACIÓN DE PÁGINA (Optimizada para celular)
st.set_page_config(
    page_title="Terminal IA - Andrés Rojas", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Estilo visual para que parezca una App nativa
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffcc; }
    .stExpander { border: 1px solid #30363d; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 AI Investment Agent")
st.caption("Estrategia y Análisis Multi-Agente | Andrés Rojas")

# --- SIDEBAR: Ajustes rápidos ---
st.sidebar.header("⚙️ Configuración")
risk = st.sidebar.select_slider("Perfil de Riesgo", options=["low", "medium", "high"], value="medium")
capital = st.sidebar.number_input("Capital Inicial ($)", value=10000, step=1000)
tickers_input = st.sidebar.text_input("Acciones (ej: AAPL, NVDA, TSLA)", "AAPL, MSFT, TSLA")

# --- LÓGICA DE EJECUCIÓN ---
if st.sidebar.button("🚀 Ejecutar Análisis"):
    setup_dependencies()
    tickers = [t.strip().upper() for t in tickers_input.split(",")]
    
    with st.spinner('Los agentes están procesando datos en tiempo real...'):
        all_reports = []
        for ticker in tickers:
            try:
                res = run_system(ticker)
                all_reports.append(res)
            except Exception as e:
                st.error(f"Error analizando {ticker}: {str(e)}")

    if all_reports:
        # ==========================================
        # 🎯 SECCIÓN 1: MÉTRICAS DE DECISIÓN
        # ==========================================
        st.header("🎯 Recomendaciones del Sistema")
        cols = st.columns(len(all_reports))
        for i, res in enumerate(all_reports):
            with cols[i]:
                st.metric(
                    label=res['ticker'], 
                    value=res['decision']['recommendation'], 
                    delta=f"Confianza: {res['decision']['confidence']}"
                )

        # ==========================================
        # 🔍 SECCIÓN 2: ANÁLISIS POR ACTIVO
        # ==========================================
        st.divider()
        st.header("🔍 Análisis Detallado")
        
        # Diccionario de traducción para ratios
        label_map = {
            "pe": "P/E Ratio",
            "roe": "ROE (Retorno s/ Patrimonio)",
            "debt_to_equity": "Ratio Deuda / Capital",
            "revenue_growth": "Crecimiento Ingresos",
            "fcf": "Free Cash Flow",
            "momentum": "Momentum (6m)",
            "volatility": "Volatilidad Anual"
        }

        for res in all_reports:
            with st.expander(f"📊 Reporte de {res['ticker']}", expanded=False):
                col_info, col_news = st.columns([1, 1.2])
                
                # --- LADO IZQUIERDO: RATIOS Y EXPLICACIÓN ---
                with col_info:
                    st.subheader("📉 Ratios Clave")
                    r = res['financials']['ratios']
                    for key, val in r.items():
                        name = label_map.get(key, key.upper())
                        # Formateo visual
                        if "fcf" in key or val > 5000:
                            v_str = f"${val:,.0f}"
                        elif val < 1 and val > -1:
                            v_str = f"{val*100:.2f}%"
                        else:
                            v_str = f"{val:.2f}"
                        st.write(f"**{name}:** {v_str}")
                    
                    st.markdown("---")
                    st.markdown("**💡 Insight del Agente:**")
                    st.info(res['explainability']['explanation'])

                # --- LADO DERECHO: NOTICIAS CON LINKS ---
                with col_news:
                    st.subheader("📰 Noticias Relacionadas")
                    score = res['sentiment']['sentiment_score']
                    
                    if score > 0.15:
                        st.success(f"Sentimiento Positivo: {score:.2f} ✅")
                    elif score < -0.15:
                        st.error(f"Sentimiento Negativo: {score:.2f} ⚠️")
                    else:
                        st.warning(f"Sentimiento Neutral: {score:.2f} ⚖️")
                    
                    st.write("Enlaces directos a la fuente:")
                    for art in res['sentiment']['articles'][:5]:
                        url = art.get('url') or "https://news.google.com"
                        st.markdown(f"🔗 **[{art['title']}]({url})**")
                        source_name = art.get('source', {}).get('name', 'Fuente Web')
                        st.caption(f"Fuente: {source_name}")
                        st.divider()

        # ==========================================
        # 💼 SECCIÓN 3: RENDIMIENTO Y PORTAFOLIO
        # ==========================================
        st.divider()
        st.header("💼 Gestión de Portafolio")
        
        p_agent = PortfolioAgent()
        portfolio_res = p_agent.run(all_reports, capital)
        
        bt_agent = BacktestingAgent()
        bt_res = bt_agent.run(portfolio_res["portfolio"])
        
        bench_agent = BenchmarkAgent()
        bench_res = bench_agent.run(bt_res["portfolio_return"])

        # Métricas Finales
        m1, m2, m3 = st.columns(3)
        m1.metric("Retorno Portafolio", f"{bt_res['portfolio_return']*100:.2f}%")
        m2.metric("Sharpe Ratio", f"{bt_res['sharpe_ratio']:.2f}")
        m3.metric("Alpha vs S&P500", f"{(bt_res['portfolio_return'] - bench_res['benchmark_return'])*100:.2f}%")

        st.write("**Distribución sugerida:**")
        df_plot = pd.DataFrame(portfolio_res["portfolio"])
        st.bar_chart(df_plot.set_index("ticker")["allocation"])

else:
    st.info("Configura los tickers en el menú lateral y haz clic en 'Iniciar Análisis' para comenzar.")