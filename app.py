import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIP PARTNER | Expertise", layout="wide")

# --- STYLE LISIBLE ET PRO ---
st.markdown("""
    <style>
    .main { background-color: #0E1117; color: #E0E0E0; }
    .stMetric { background-color: #1A1F26; padding: 15px; border-radius: 10px; border-left: 5px solid #B5A27B; }
    h1, h2 { color: #B5A27B !important; }
    .stButton>button { background-color: #B5A27B; color: #0A1A3F; width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- SÉCURITÉ LOGO ---
def load_logo():
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", width=200)
    else:
        st.sidebar.title("💎 VIP PARTNER")
        st.sidebar.warning("Logo.png manquant sur GitHub")

# --- LOGIQUE MÉTIER CGP ---
def calcul_ir(revenu_net_imposable, parts=1):
    """Calcul simplifié de l'Impôt sur le Revenu 2024/2025 (Barème Progressif)"""
    quotient = revenu_net_imposable / parts
    impot = 0
    if quotient > 177106:
        impot += (quotient - 177106) * 0.45
        quotient = 177106
    if quotient > 82341:
        impot += (quotient - 82341) * 0.41
        quotient = 82341
    if quotient > 28797:
        impot += (quotient - 28797) * 0.30
        quotient = 28797
    if quotient > 11294:
        impot += (quotient - 11294) * 0.11
    return round(impot * parts)

# --- INTERFACE ---
load_logo()
menu = st.sidebar.radio("Expertise", ["Marchés & Actifs", "Immobilier (LMNP/Pinel)", "Audit Fiscal (IR)", "Projection Retraite"])

if menu == "Marchés & Actifs":
    st.title("📈 Analyse des Supports")
    ticker = st.text_input("Rechercher un actif (ex: CW8.PA, AI.PA, BTC-USD)", "CW8.PA")
    
    try:
        data = yf.download(ticker, period="1y")
        if not data.empty:
            fig = go.Figure(data=[go.Scatter(x=data.index, y=data['Close'], line=dict(color='#B5A27B', width=2))])
            fig.update_layout(template="plotly_dark", title=f"Évolution 12 mois : {ticker}", xaxis_title="Date", yaxis_title="Prix")
            st.plotly_chart(fig, use_container_width=True)
            
            c1, c2 = st.columns(2)
            c1.metric("Dernier Cours", f"{data['Close'].iloc[-1]:.2f} €")
            perf = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            c2.metric("Performance 12m", f"{perf:.2f}%")
        else:
            st.error("Données indisponibles pour ce ticker.")
    except:
        st.error("Erreur lors de la récupération des données.")

elif menu == "Audit Fiscal (IR)":
    st.title("⚖️ Optimisation Fiscale")
    col1, col2 = st.columns(2)
    with col1:
        rni = st.number_input("Revenu Net Imposable (€)", value=50000, step=1000)
        parts = st.number_input("Nombre de parts", value=1.0, step=0.5)
    
    impot_total = calcul_ir(rni, parts)
    tmi = 0
    # Calcul TMI rapide
    q = rni/parts
    if q > 177106: tmi = 45
    elif q > 82341: tmi = 41
    elif q > 28797: tmi = 30
    elif q > 11294: tmi = 11
    
    with col2:
        st.metric("Impôt estimé", f"{impot_total} €")
        st.metric("Tranche Marginale (TMI)", f"{tmi}%")
    
    st.info(f"Une souscription au PER de 5 000 € vous ferait économiser environ {5000 * (tmi/100):.0f} € d'impôt.")

elif menu == "Immobilier (LMNP/Pinel)":
    st.title("🏠 Simulation Immobilier")
    px = st.number_input("Prix d'achat", value=150000)
    loyer = st.number_input("Loyer mensuel HC", value=650)
    rendement = (loyer * 12 / px) * 100
    st.metric("Rendement Brut", f"{rendement:.2f}%")
    st.write("Le régime LMNP (Loueur Meublé Non Professionnel) permettrait d'amortir le bien sur 25 ans, neutralisant l'impôt sur les loyers.")

elif menu == "Projection Retraite":
    st.title("⏳ Horizon Patrimonial")
    age = st.slider("Âge actuel", 20, 65, 30)
    versement = st.number_input("Versement mensuel (€)", value=300)
    taux = st.slider("Rendement espéré (%)", 1, 10, 5)
    
    annees = 65 - age
    capital = 0
    for _ in range(annees * 12):
        capital = (capital + versement) * (1 + (taux/100)/12)
    
    st.success(f"À 65 ans, votre capital projeté est de : {capital:,.0f} €")
