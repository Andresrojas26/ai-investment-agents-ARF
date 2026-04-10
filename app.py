import streamlit as st
import pandas as pd
import sys
import os

# Asegurar que encuentre los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import run_system, setup_dependencies
from agents.portfolio_agent import PortfolioAgent
from agents.backtesting_agent import BacktestingAgent
from agents.benchmark_agent import BenchmarkAgent

# Configuración de la página para que se vea bien en móviles
st.set_page_config(
    page_title="AI Investment Terminal", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Estilo personalizado para mejorar la estética
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 AI Investment Agent Terminal")
st.caption("Desarrollado por Andrés Rojas - Civil Industrial Engineering")

# --- SIDEBAR: Configuración ---
st.sidebar.header("👤 Configuración")
risk = st.sidebar.select_slider("Riesgo", options=["low", "medium", "high"])
capital = st.sidebar.number_input("Capital ($)", value=10000)
tickers_input = st.sidebar.text_input("Tickers (separados por coma)", "AAPL, MSFT, TSLA")

if st.sidebar.button("🚀 Iniciar Análisis"):
    setup_dependencies()
    tickers = [t.strip().upper() for t in tickers_input.split(",")]
    
    with st.spinner('Agentes analizando mercado...'):
        all_reports = []
        for ticker in tickers:
            res = run_system(ticker)
            all_reports.append(res)
    
    # ==========================================
    # 💼 SECCIÓN 1: RESUMEN DE RECOMENDACIONES
    # ==========================================
    st.header("🎯 Recomendaciones")
    cols = st.columns(len(all_reports))
    for i, res in enumerate(all_reports):
        with cols[i]:
            st.metric(
                label=f"Acción: {res['ticker']}", 
                value=res['decision']['recommendation'], 
                delta=f"Confianza: {res['decision']['confidence']}"
            )

    # ==========================================
    # 🔍 SECCIÓN 2: DETALLE PROFUNDO (UI LIMPIA)
    # ==========================================
    st.divider()
    st.header("🔍 Análisis Detallado")
    
    # Mapa para limpiar los nombres de los ratios
    label_map = {
        "pe": "P/E Ratio",
        "roe": "ROE (Retorno s/ Patrimonio)",
        "debt_to_equity": "Deuda / Capital",
        "revenue_growth": "Crecimiento de Ingresos",
        "fcf": "Free Cash Flow",
        "momentum": "Momentum de Precio",
        "volatility": "Volatilidad"
    }

    for res in all_reports:
        with st.expander(f"📊 Ver reporte completo de {res['ticker']}", expanded=False):
            col_left, col_right = st.columns([1, 1.5])
            
            # --- COLUMNA IZQUIERDA: RATIOS ---
            with col_left:
                st.subheader("📉 Ratios Financieros")
                ratios = res['financials']['ratios']
                for key, val in ratios.items():
                    name = label_map.get(key, key.upper())
                    # Formateo de valores
                    if "fcf" in key or val > 1000:
                        val_str = f"${val:,.0f}"
                    elif "growth" in key or "roe" in key:
                        val_str = f"{val*100:.2f}%" if val < 1 else f"{val:.2f}"
                    else:
                        val_str = f"{val:.2f}"
                    
                    st.write(f"**{name}:** {val_str}")
                
                st.info(f"**Explicación IA:** {res['explainability']['explanation']}")

            # --- COLUMNA DERECHA: NOTICIAS ---
            with col_right:
                st.subheader("📰 Sentimiento del Mercado")
                score = res['sentiment']['sentiment_score']
                
                if score > 0.15:
                    st.success(f"Sentimiento Positivo: {score:.2f} ✅")
                elif score < -0.15:
                    st.error(f"Sentimiento Negativo: {score:.2f} ⚠️")
                else:
                    st.warning(f"Sentimiento Neutral: {score:.2f} ⚖️")
                
                st.markdown("**Últimas Noticias & Resúmenes:**")
                for art in res['sentiment']['articles'][:3]:
                    st.markdown(f"🔹 **[{art['title']}]({art.get('url', '#')})**")
                    resumen = art.get('description') or "No hay resumen disponible para esta noticia."
                    st.caption(f"_{resumen}_")
                    st.divider()

    # ==========================================
    # 💹 SECCIÓN 3: PORTAFOLIO & BACKTESTING
    # ==========================================
    st.divider()
    st.header("💼 Gestión de Portafolio")
    
    p_agent = PortfolioAgent()
    portfolio_res = p_agent.run(all_reports, capital)
    
    bt_agent = BacktestingAgent()
    bt_res = bt_agent.run(portfolio_res["portfolio"])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Retorno Portafolio", f"{bt_res['portfolio_return']*100:.2f}%")
    m2.metric("Sharpe Ratio", f"{bt_res['sharpe_ratio']:.2f}")
    m3.metric("Volatilidad", f"{bt_res['volatility']:.4f}")

    # Gráfico de distribución
    st.write("**Distribución Sugerida de Capital:**")
    df_p = pd.DataFrame(portfolio_res["portfolio"])
    st.bar_chart(df_p.set_index("ticker")["allocation"])