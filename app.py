import streamlit as st
import pandas as pd
from main import run_system # Importamos tu lógica existente

# Configuración de la página
st.set_page_config(page_title="AI Investment Terminal", layout="wide")

st.title("🤖 AI Investment Agent Terminal")
st.markdown("Análisis multi-agente de activos financieros")

# --- SIDEBAR: Configuración del Usuario ---
st.sidebar.header("Configuración del Perfil")
risk = st.sidebar.select_slider("Nivel de Riesgo", options=["low", "medium", "high"])
horizon = st.sidebar.selectbox("Horizonte de Inversión", ["short", "long"])
tickers_input = st.sidebar.text_input("Tickers (separados por coma)", "AAPL, MSFT, TSLA")

# --- BOTÓN DE EJECUCIÓN ---
if st.sidebar.button("Ejecutar Análisis"):
    tickers = [t.strip().upper() for t in tickers_input.split(",")]
    
    with st.spinner('Los agentes están trabajando...'):
        results = []
        for ticker in tickers:
            # Aquí podrías pasar risk y horizon como parámetros si los integras en run_system
            res = run_system(ticker)
            results.append(res)
    
    # --- VISUALIZACIÓN DE RESULTADOS ---
    st.success("Análisis Completado")
    
    # Ranking Rápido en la parte superior
    cols = st.columns(len(results))
    for i, res in enumerate(results):
        with cols[i]:
            st.metric(label=res['ticker'], 
                      value=res['decision']['recommendation'], 
                      delta=f"Confianza: {res['decision']['confidence']}")

    # Tabs para detalles profundos
    for res in results:
        with st.expander(f"Ver Análisis Detallado de {res['ticker']}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Ratios Financieros")
                st.json(res['financials']['ratios'])
                
            with col2:
                st.subheader("📰 Sentimiento de Noticias")
                st.write(f"Score Global: {res['sentiment']['sentiment_score']}")
                for art in res['sentiment']['articles'][:3]:
                    st.caption(f"• {art['title']} ({art['sentiment']})")

            st.divider()
            st.subheader("🧠 Explicación del Agente")
            st.info(res['explainability']['explanation'])
            
            if res["alert"]["alert"]:
                st.warning(f"🚨 ALERTA: {res['alert']['message']}")