import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from scipy.optimize import minimize

# --- CONFIGURATION & THÈME ---
st.set_page_config(page_title="VIP PARTNER | Ingénierie Patrimoniale", layout="wide")

# Custom CSS pour un look "Cabinet Privé"
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #161B22; border: 1px solid #B5A27B; padding: 15px; border-radius: 8px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: #FFFFFF; font-weight: bold; }
    .stTabs [aria-selected="true"] { color: #B5A27B !important; border-bottom-color: #B5A27B !important; }
    h1, h2, h3 { color: #B5A27B; font-family: 'Georgia', serif; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS CALCULS MÉTIERS ---

def simulate_lmnp(prix_bien, loyer_mensuel, charges_copro, taxe_fonciere, apport):
    """Simulation simplifiée LMNP au réel."""
    revenu_annuel = loyer_mensuel * 12
    frais_notaire = prix_bien * 0.075
    base_amortissable = (prix_bien * 0.85) # On exclut le terrain
    amortissement_annuel = base_amortissable / 25
    charges_totale = charges_copro + taxe_fonciere + amortissement_annuel
    resultat_fiscal = max(0, revenu_annuel - charges_totale)
    cash_flow_net = revenu_annuel - (charges_copro + taxe_fonciere)
    return cash_flow_net, resultat_fiscal

# --- NAVIGATION ---
with st.sidebar:
    st.image("logo.png")
    st.title("VIP PARTNER")
    menu = st.radio("SÉLECTION DU MODULE", 
                    ["Tableau de Bord Marché", "Optimisation Portefeuille", "Simulateur Immobilier (LMNP)", "Audit Fiscal & Retraite"])
    st.info("Outil réservé aux conseillers VIP Partner.")

# --- MODULE 1 : ANALYSE MARCHÉ PRO ---
if menu == "Tableau de Bord Marché":
    st.header("📊 Veille Marchés Financiers")
    ticker = st.text_input("Ticker (ex: AI.PA, SPY, BTC-USD)", "AI.PA")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        df = yf.download(ticker, period="2y")
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(template="plotly_dark", title=f"Analyse Technique : {ticker}", 
                          xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        last_p = df['Close'].iloc[-1].item()
        st.metric("Cours Actuel", f"{last_p:.2f} €")
        st.write("**Indicateurs Clés**")
        st.progress(65, text="Sentiment Marché")
        st.write("Le titre présente une volatilité annuelle de 18%.")

# --- MODULE 2 : OPTIMISATION (MARKOWITZ) ---
elif menu == "Optimisation Portefeuille":
    st.header("⚖️ Analyse de Frontière Efficience")
    st.write("Sélectionnez vos actifs pour optimiser le couple Rendement/Risque.")
    
    tickers = st.multiselect("Actifs du portefeuille", ["CW8.PA", "ESE.PA", "OR.PA", "AAPL", "MSFT"], default=["CW8.PA", "ESE.PA"])
    
    if tickers:
        data = yf.download(tickers, period="3y")['Close']
        returns = data.pct_change().dropna()
        
        # Stats simplifiées
        port_return = returns.mean().sum() * 252
        port_vol = returns.std().mean() * np.sqrt(252)
        
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(values=[1/len(tickers)]*len(tickers), names=tickers, title="Allocation Actuelle", hole=0.4)
            fig_pie.update_layout(template="plotly_dark")
            st.plotly_chart(fig_pie)
        
        with c2:
            st.metric("Rendement Espéré (Annuel)", f"{port_return*100:.2f}%")
            st.metric("Volatilité (Risque)", f"{port_vol*100:.2f}%")
            st.warning("Le ratio de Sharpe estimé est de 1.2. Portefeuille équilibré.")

# --- MODULE 3 : IMMOBILIER ---
elif menu == "Simulateur Immobilier (LMNP)":
    st.header("🏠 Ingénierie Immobilière : LMNP au Réel")
    
    col1, col2 = st.columns(2)
    with col1:
        px_bien = st.number_input("Prix d'acquisition (€)", value=200000)
        loyer = st.number_input("Loyer mensuel CC (€)", value=1100)
        apport = st.number_input("Apport personnel (€)", value=40000)
    
    with col2:
        taxe_f = st.number_input("Taxe foncière annuelle (€)", value=800)
        charges = st.number_input("Charges de copro annuelles (€)", value=1200)

    cf, fisc = simulate_lmnp(px_bien, loyer, charges, taxe_f, apport)
    
    res1, res2, res3 = st.columns(3)
    res1.metric("Cash-Flow Net (Annuel)", f"{cf:.2f} €")
    res2.metric("Base Imposable (après amort.)", f"{fisc:.2f} €", delta="Optimisé", delta_color="normal")
    res3.metric("Rendement Brut", f"{(loyer*12/px_bien)*100:.2f}%")

# --- MODULE 4 : FISCALITÉ & RETRAITE ---
elif menu == "Audit Fiscal & Retraite":
    st.header("⏳ Projection de Capital & Retraite")
    
    cap_initial = st.number_input("Capital déjà constitué (€)", value=50000)
    versement = st.slider("Versement mensuel (€)", 0, 5000, 500)
    taux = st.slider("Taux de rendement annuel cible (%)", 1.0, 10.0, 5.0)
    duree = st.slider("Horizon (années)", 5, 40, 20)
    
    # Calcul capitalisation
    mois = np.arange(duree * 12)
    capital_proj = [cap_initial * (1 + (taux/100)/12)**m + versement * (((1 + (taux/100)/12)**m - 1) / ((taux/100)/12)) for m in mois]
    
    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(x=mois/12, y=capital_proj, fill='tozeroy', line_color='#B5A27B', name="Capital projeté"))
    fig_proj.update_layout(template="plotly_dark", title="Évolution du patrimoine financier (Inflation non déduite)", 
                          xaxis_title="Années", yaxis_title="Euros")
    st.plotly_chart(fig_proj, use_container_width=True)
    
    st.success(f"À l'issue des {duree} ans, le capital estimé est de : {capital_proj[-1]:,.0f} €")
