import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="VIP PARTNER | Outils CGP", layout="wide", page_icon="💎")

# --- STYLE CSS CIBLÉ ET PROPRE ---
st.markdown("""
    <style>
    /* On stylise uniquement les blocs de métriques pour qu'ils ressortent proprement */
    div[data-testid="metric-container"] {
        background-color: rgba(181, 162, 123, 0.1);
        border-left: 5px solid #B5A27B;
        padding: 10px 20px;
        border-radius: 5px;
    }
    h1, h2, h3 { color: #B5A27B !important; font-family: 'Arial', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS MÉTIERS CGP ---
def calcul_ir(rni, parts):
    """Calcul de l'IR avec le barème 2024"""
    q = rni / parts
    impot = 0
    if q > 177106: impot += (q - 177106) * 0.45; q = 177106
    if q > 82341: impot += (q - 82341) * 0.41; q = 82341
    if q > 28797: impot += (q - 28797) * 0.30; q = 28797
    if q > 11294: impot += (q - 11294) * 0.11
    return round(impot * parts)

# --- GESTION DU LOGO ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
else:
    st.sidebar.markdown("## 💎 VIP PARTNER")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Boîte à outils CGP", [
    "1. Marchés Financiers", 
    "2. Intérêts Composés", 
    "3. Crédit & Immobilier", 
    "4. Fiscalité (IR & IFI)", 
    "5. Transmission & Succession"
])

# ==========================================
# MODULE 1 : MARCHÉS FINANCIERS
# ==========================================
if menu == "1. Marchés Financiers":
    st.title("📈 Analyse des Supports")
    ticker = st.text_input("Ticker Yahoo Finance (ex: CW8.PA, AI.PA, BTC-USD)", "CW8.PA")
    
    try:
        # Utilisation de Ticker().history() au lieu de download() pour éviter les bugs
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")
        
        if not data.empty:
            c1, c2, c3 = st.columns(3)
            current_price = data['Close'].iloc[-1]
            first_price = data['Close'].iloc[0]
            perf = ((current_price / first_price) - 1) * 100
            volatility = data['Close'].pct_change().std() * np.sqrt(252) * 100
            
            c1.metric("Dernier Cours", f"{current_price:.2f} €")
            c2.metric("Performance 1 an", f"{perf:.2f} %")
            c3.metric("Volatilité annualisée", f"{volatility:.2f} %")
            
            fig = go.Figure(data=[go.Scatter(x=data.index, y=data['Close'], line=dict(color='#B5A27B', width=2))])
            fig.update_layout(title=f"Historique 1 an - {ticker}", xaxis_title="Date", yaxis_title="Prix")
            # Le paramètre theme="streamlit" adapte les couleurs au mode clair/sombre du client
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        else:
            st.warning("Aucune donnée trouvée pour ce ticker.")
    except Exception as e:
        st.error(f"Erreur de connexion aux marchés : {e}")

# ==========================================
# MODULE 2 : INTÉRÊTS COMPOSÉS
# ==========================================
elif menu == "2. Intérêts Composés":
    st.title("💰 Capitalisation & Épargne")
    
    col1, col2, col3, col4 = st.columns(4)
    capital_depuis = col1.number_input("Capital initial (€)", value=10000, step=1000)
    versement_mensuel = col2.number_input("Versement mensuel (€)", value=300, step=50)
    taux_annuel = col3.number_input("Taux annuel net (%)", value=5.0, step=0.5)
    annees = col4.slider("Durée (Années)", 1, 40, 20)
    
    mois = annees * 12
    taux_mensuel = (taux_annuel / 100) / 12
    
    # Calculs de l'évolution
    historique_capital = []
    capital_actuel = capital_depuis
    total_versements = capital_depuis
    
    for _ in range(mois):
        capital_actuel = capital_actuel * (1 + taux_mensuel) + versement_mensuel
        total_versements += versement_mensuel
        historique_capital.append(capital_actuel)
        
    interets_gagnes = capital_actuel - total_versements
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Capital Final Bruit", f"{capital_actuel:,.0f} €".replace(',', ' '))
    c2.metric("Total des versements", f"{total_versements:,.0f} €".replace(',', ' '))
    c3.metric("Intérêts générés", f"{interets_gagnes:,.0f} €".replace(',', ' '))
    
    # Graphique
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=historique_capital, x=np.arange(1, mois+1)/12, name="Capital Total", fill='tozeroy', line_color='#B5A27B'))
    fig.update_layout(title="Évolution du patrimoine dans le temps", xaxis_title="Années", yaxis_title="Euros")
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

# ==========================================
# MODULE 3 : CRÉDIT & IMMOBILIER
# ==========================================
elif menu == "3. Crédit & Immobilier":
    st.title("🏠 Capacité d'emprunt & Crédit")
    
    st.subheader("Simulateur de Crédit Immobilier")
    col1, col2, col3 = st.columns(3)
    montant_emprunte = col1.number_input("Montant à emprunter (€)", value=200000, step=5000)
    taux_credit = col2.number_input("Taux du crédit (%)", value=3.5, step=0.1)
    duree_ans = col3.slider("Durée du prêt (Années)", 5, 30, 20)
    
    # Formule mathématique de la mensualité de crédit
    t_mensuel = (taux_credit / 100) / 12
    n_mois = duree_ans * 12
    if t_mensuel > 0:
        mensualite = (montant_emprunte * t_mensuel) / (1 - (1 + t_mensuel)**(-n_mois))
    else:
        mensualite = montant_emprunte / n_mois
        
    cout_total_credit = (mensualite * n_mois) - montant_emprunte
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Mensualité (hors assurance)", f"{mensualite:.2f} € / mois")
    c2.metric("Coût total du crédit", f"{cout_total_credit:,.0f} €".replace(',', ' '))
    
    salaire_net = st.number_input("Revenus nets mensuels de l'emprunteur (€)", value=4000, step=100)
    taux_endettement = (mensualite / salaire_net) * 100
    c3.metric("Taux d'endettement estimé", f"{taux_endettement:.1f} %")
    if taux_endettement > 35:
        st.error("⚠️ Attention : Le taux d'endettement dépasse la limite du HCSF (35%).")

# ==========================================
# MODULE 4 : FISCALITÉ
# ==========================================
elif menu == "4. Fiscalité (IR & IFI)":
    st.title("⚖️ Audit Fiscal")
    
    tab1, tab2 = st.tabs(["Impôt sur le Revenu (IR)", "Impôt sur la Fortune Immobilière (IFI)"])
    
    with tab1:
        st.subheader("Calcul
