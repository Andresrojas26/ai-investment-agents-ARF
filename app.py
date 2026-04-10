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

# 1. CONFIGURACIÓN DE PÁGINA (Mobile First)
st.set_page_config(
    page_title="Terminal IA - Andrés Rojas", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Estilo visual profesional
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffcc; }
    .stExpander { border: 1px solid #30363d; border-radius: 8px; margin-bottom: 1rem; }
    .stCaption { font-size: 0.85rem; color: #8b949e; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 AI Investment Agent")
st.caption("Estrategia y Análisis Multi-Agente | Andrés Rojas - Civil Industrial Engineering")

# --- SIDEBAR: Configuración ---
st.sidebar.header("⚙️ Panel de Control")
risk = st.sidebar.select_slider("Perfil de Riesgo", options=["low", "medium", "high"], value="medium")
capital = st.sidebar.number_input("Capital Inicial ($)", value=10000, step=1000)
tickers_input = st.sidebar.text_input("Acciones (ej: AAPL, NVDA, TSLA)", "AAPL, MSFT, NVDA, F")

# --- BOTÓN DE EJECUCIÓN ---
if st.sidebar.button("🚀 Iniciar Análisis"):
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
        # 🎯 SECCIÓN 1: MÉTRICAS DE RESUMEN
        # ==========================================
        st.header("🎯 Recomendaciones")
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
                
                # --- IZQUIERDA: RATIOS Y EXPLICACIÓN ---
                with col_info:
                    st.subheader("📉 Ratios Clave")
                    r = res['financials'].get('ratios', {})
                    for key, val in r.items():
                        name = label_map.get(key, key.upper())
                        
                        # --- SOLUCIÓN AL ERROR DE TYPEERROR (VALORES NONE) ---
                        if val is not None:
                            try:
                                if "fcf" in key or (isinstance(val, (int, float)) and val > 5000):
                                    v_str = f"${val:,.0f}"
                                elif isinstance(val, (int, float)) and -1 < val < 1:
                                    v_str = f"{val*100:.2f}%"
                                else:
                                    v_str = f"{val:.2f}"
                            except:
                                v_str = str(val)
                        else:
                            v_str = "N/A"
                        
                        st.write(f"**{name}:** {v_str}")
                    
                    st.markdown("---")
                    st.markdown("**💡 Análisis de la IA:**")
                    st.info(res['explainability']['explanation'])

                # --- DERECHA: NOTICIAS REALES CON LINKS ---
                with col_news:
                    st.subheader("📰 Noticias Relacionadas")
                    score = res['sentiment']['sentiment_score']
                    
                    if score > 0.15:
                        st.success(f"Sentimiento Positivo: {score:.2f} ✅")
                    elif score < -0.15:
                        st.error(f"Sentimiento Negativo: {score:.2f} ⚠️")
                    else:
                        st.warning(f"Sentimiento Neutral: {score:.2f} ⚖️")
                    
                    st.write("Enlaces directos verificados:")
                    
                    articles = res['sentiment'].get('articles', [])
                    if not articles:
                        st.write("No se encontraron noticias recientes.")
                    else:
                        for art in articles[:5]:
                            link_real = art.get('url')
                            titulo = art.get('title', 'Noticia sin título')
                            nombre_fuente = art.get('source', {}).get('name', 'Fuente Externa')

                            if link_real and str(link_real).startswith('http'):
                                st.markdown(f"🔗 **[{titulo}]({link_real})**")
                                st.caption(f"Fuente: {nombre_fuente}")
                            else:
                                st.write(f"🔹 {titulo}")
                                st.caption(f"Fuente: {nombre_fuente} (Link no disponible)")
                            
                            st.divider()

        # ==========================================
        # 💼 SECCIÓN 3: PORTAFOLIO & RENDIMIENTO
        # ==========================================
        st.divider()
        st.header("💼 Gestión de Portafolio")
        
        p_agent = PortfolioAgent()
        portfolio_res = p_agent.run(all_reports, capital)
        
        bt_agent = BacktestingAgent()
        bt_res = bt_agent.run(portfolio_res["portfolio"])
        
        bench_agent = BenchmarkAgent()
        bench_res = bench_agent.run(bt_res["portfolio_return"])

        m1, m2, m3 = st.columns(3)
        m1.metric("Retorno Portafolio", f"{bt_res['portfolio_return']*100:.2f}%")
        m2.metric("Sharpe Ratio", f"{bt_res['sharpe_ratio']:.2f}")
        m3.metric("Alpha vs Mercado", f"{(bt_res['portfolio_return'] - bench_res['benchmark_return'])*100:.2f}%")

        st.write("**Distribución sugerida del capital:**")
        df_plot = pd.DataFrame(portfolio_res["portfolio"])
        st.bar_chart(df_plot.set_index("ticker")["allocation"])

else:
    st.info("Configura los tickers en el menú lateral y presiona 'Iniciar Análisis'.")